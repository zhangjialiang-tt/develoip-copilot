// Custom Tools: the ONLY model-callable path into the Python Runtime.
// Tools translate parameters to bridge ops; they never keep Runtime state.
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import type { BridgeClient } from "./bridge";

interface ToolResult {
  content: { type: "text"; text: string }[];
  details: unknown;
}

function text(value: unknown): ToolResult {
  const rendered = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return { content: [{ type: "text", text: rendered }], details: value };
}

interface HelloResult {
  role_request_fields: string[];
  role_response_fields: string[];
  forbidden_role_fields: string[];
}

export function registerTools(pi: ExtensionAPI, bridge: BridgeClient): void {
  const { z } = pi.zod;

  pi.registerTool({
    name: "dc_dispatch",
    label: "DC Dispatch",
    description:
      "Submit one Runtime Command to the develoip-copilot Runtime (single write entry point). The command needs command_id, command_type, actor, optional target_ref and payload. Ownership, Approval, Baseline and Scope checks happen in the Runtime; rejections are returned as errors.",
    parameters: z.object({
      command: z.record(z.string(), z.unknown()).describe("Runtime Command object"),
    }),
    hidden: false,
    defaultInactive: false,
    async execute(_id: string, params: { command: Record<string, unknown> }): Promise<ToolResult> {
      const command = { ...params.command };
      if (!command.command_id) command.command_id = `cmd-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
      const result = await bridge.request("dispatch", { command });
      return text(result);
    },
  });

  pi.registerTool({
    name: "dc_query",
    label: "DC Query",
    description:
      "Read Runtime state. With summary=true (or no object_id) returns Task/Approval/Blocker/Gate status and next legal actions; otherwise returns one object by id. OMP must never answer progress questions from session memory — always query here.",
    parameters: z.object({
      object_id: z.string().optional(),
      object_type: z.string().optional(),
      summary: z.boolean().optional(),
    }),
    hidden: false,
    defaultInactive: false,
    async execute(_id: string, params: { object_id?: string; object_type?: string; summary?: boolean }): Promise<ToolResult> {
      if (params.summary || !params.object_id) {
        return text(await bridge.request("status"));
      }
      return text(await bridge.request("query", { object_id: params.object_id, object_type: params.object_type }));
    },
  });

  pi.registerTool({
    name: "dc_restore",
    label: "DC Restore",
    description:
      "Restore Runtime state from the Event Store (after OMP restart or bridge crash). Never rebuild state from chat history.",
    parameters: z.object({}),
    hidden: false,
    defaultInactive: false,
    async execute(): Promise<ToolResult> {
      const restored = await bridge.request("restore");
      const status = await bridge.request("status");
      return text({ restored, status });
    },
  });

  pi.registerTool({
    name: "dc_invoke_role",
    label: "DC Invoke Role",
    description:
      "Prepare a contract role invocation. Validates the role request, then instructs the main agent to run the OMP task subagent for that role and to feed the structured output back through dc_submit_candidates. Roles never write state directly.",
    parameters: z.object({
      role: z.enum(["orchestrator", "system-investigator", "rtl-engineer", "verification-engineer", "integration-reviewer", "documenter"]),
      task_ref: z.string(),
      baseline_ref: z.string(),
      expected_output: z.string(),
      completion_criteria: z.string(),
      scope: z.object({ paths: z.array(z.string()) }).optional(),
      approval_refs: z.array(z.string()).optional(),
      instructions: z.string().optional(),
    }),
    hidden: false,
    defaultInactive: false,
    async execute(_id: string, params: {
      role: string;
      task_ref: string;
      baseline_ref: string;
      expected_output: string;
      completion_criteria: string;
      scope?: { paths: string[] };
      approval_refs?: string[];
      instructions?: string;
    }): Promise<ToolResult> {
      const hello = (await bridge.request("hello")) as HelloResult;
      const request = {
        role: params.role,
        task_ref: params.task_ref,
        scope: params.scope ?? { paths: [] },
        approval_refs: params.approval_refs ?? [],
        baseline_ref: params.baseline_ref,
        expected_output: params.expected_output,
        completion_criteria: params.completion_criteria,
      };
      const missing = hello.role_request_fields.filter((field) => !(field in request));
      if (missing.length > 0) {
        throw new Error(`Role request missing fields: ${missing.join(", ")}`);
      }
      return text({
        role_request: request,
        next_step:
          `Run the OMP 'task' tool with one subagent acting as '${params.role}'. ` +
          "The subagent must finish with a single JSON object using EXACTLY the allowed role output fields " +
          `(${hello.role_response_fields.join(", ")}). ` +
          `Forbidden fields: ${hello.forbidden_role_fields.join(", ")}. ` +
          "Then submit that JSON via dc_submit_candidates with this same request object.",
        additional_instructions: params.instructions ?? "",
      });
    },
  });

  pi.registerTool({
    name: "dc_submit_candidates",
    label: "DC Submit Candidates",
    description:
      "Validate a role's structured output through the RoleInvocationLayer and convert it into candidate Runtime Commands. Candidates are proposals only; dispatch each accepted candidate via dc_dispatch.",
    parameters: z.object({
      request: z.record(z.string(), z.unknown()).describe("The role request used for dc_invoke_role"),
      output: z.record(z.string(), z.unknown()).describe("The role's structured output"),
      actor: z.string().optional().describe("Runtime actor; defaults to the role name"),
    }),
    hidden: false,
    defaultInactive: false,
    async execute(_id: string, params: { request: Record<string, unknown>; output: Record<string, unknown>; actor?: string }): Promise<ToolResult> {
      const result = await bridge.request("submit_candidates", params);
      return text(result);
    },
  });

  pi.registerTool({
    name: "dc_workspace_status",
    label: "DC Workspace Status",
    description: "Report pilot workspace connection state, classification, branch/commit and Runtime-managed state location.",
    parameters: z.object({}),
    hidden: false,
    defaultInactive: false,
    async execute(): Promise<ToolResult> {
      return text(await bridge.request("workspace_status"));
    },
  });

  pi.registerTool({
    name: "dc_capture_baseline",
    label: "DC Capture Baseline",
    description:
      "Capture a real pilot-workspace Baseline (read-only): git commit + relevant file hashes + tool versions + input refs, plus the workspace classification. Bind the result to a Task via BIND_BASELINE (dc_dispatch).",
    parameters: z.object({
      relevant_paths: z.array(z.string()).optional(),
      read_scope: z.object({ paths: z.array(z.string()) }).optional(),
      tool_versions: z.record(z.string(), z.string()).optional(),
      input_data_refs: z.array(z.string()).optional(),
    }),
    hidden: false,
    defaultInactive: false,
    async execute(_id: string, params: { relevant_paths?: string[]; read_scope?: { paths: string[] }; tool_versions?: Record<string, string>; input_data_refs?: string[] }): Promise<ToolResult> {
      const result = await bridge.request("capture_baseline", params);
      return text(result);
    },
  });
}
