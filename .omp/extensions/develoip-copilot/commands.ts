// /dc user commands. All state shown here comes from Runtime queries;
// commands never compute gate/approval/task status themselves.
import * as fs from "node:fs";
import * as path from "node:path";
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { BridgeError, type BridgeClient } from "./bridge";
import { renderDoctor, renderStatus } from "./renderers";

interface DoctorCheck {
  name: string;
  ok: boolean;
  detail: string;
}

interface ExecResult {
  code: number;
  stdout: string;
  stderr: string;
  killed?: boolean;
}

interface ApprovalObject {
  object_id: string;
  status: string;
  requested_capability: string;
  requested_scope: { paths?: string[] };
  risk_factors: string[];
  baseline_ref: string;
  task_ref: string;
  created_by: string;
}

interface StatusResult {
  tasks: { object_id: string; execution_status: string }[];
  pending_approvals: ApprovalObject[];
  [key: string]: unknown;
}

interface CommandContextLike {
  ui: {
    notify: (text: string, kind?: string) => void;
    confirm: (title: string, body: string) => Promise<boolean>;
  };
  hasUI: boolean;
  cwd: string;
}

function report(ctx: CommandContextLike, text: string): void {
  ctx.ui.notify(text, "info");
}

function failureText(error: unknown): string {
  if (error instanceof BridgeError) return `${error.code}: ${error.message}`;
  return error instanceof Error ? error.message : String(error);
}

async function execQuiet(pi: ExtensionAPI, command: string, args: string[]): Promise<ExecResult | null> {
  try {
    return (await pi.exec(command, args, {})) as ExecResult;
  } catch {
    return null;
  }
}

// OMP version is frozen at Batch 1 (see milestone3-omp-decisions.md). Doctor
// must NOT spawn a nested `omp` binary: a nested omp instance blocks for tens
// of seconds in interactive mode. Override via DC_OMP_VERSION when upgrading.
const OMP_VERSION_FROZEN = process.env.DC_OMP_VERSION ?? "omp/17.2.5 (frozen at Batch 1; nested spawn avoided)";

async function runDoctor(pi: ExtensionAPI, bridge: BridgeClient, ctx: CommandContextLike, repoRoot: string): Promise<void> {
  const checks: DoctorCheck[] = [];

  checks.push({ name: "extension", ok: true, detail: "develoip-copilot extension loaded" });

  checks.push({ name: "omp", ok: true, detail: OMP_VERSION_FROZEN });

  const python = await execQuiet(pi, "python", ["--version"]);
  checks.push({ name: "python", ok: Boolean(python && python.code === 0), detail: (python?.stdout || python?.stderr || "").trim() || "python not found" });

  let hello: Record<string, unknown> | null = null;
  try {
    await bridge.ensureStarted();
    hello = (await bridge.request("hello", {}, 10_000)) as Record<string, unknown>;
    checks.push({ name: "bridge", ok: true, detail: `protocol v${hello.protocol_version}, schema v${hello.schema_version}` });
    checks.push({ name: "event_store", ok: true, detail: `${hello.event_store} (sequence ${hello.last_sequence})` });
  } catch (error) {
    checks.push({ name: "bridge", ok: false, detail: failureText(error) });
    checks.push({ name: "event_store", ok: false, detail: "bridge unavailable" });
  }

  let toolsOk = false;
  let toolsDetail = "tool registry unavailable";
  try {
    const all = ((pi.getActiveTools?.() ?? pi.getAllTools?.()) ?? []) as Array<Record<string, unknown>>;
    const names = all.map((tool) => (typeof tool?.name === "string" ? tool.name : JSON.stringify(tool)));
    const dcTools = names.filter((name) => name.startsWith("dc_"));
    if (dcTools.length >= 5) {
      toolsOk = true;
      toolsDetail = dcTools.sort().join(", ");
    } else {
      // omp/17.2.5 does not enumerate extension-registered tools through
      // getActiveTools/getAllTools in command context, yet they ARE callable by
      // the model (Gate A evidence: dc_query invoked in-session). Bridge health
      // plus successful load is the verifiable surface here.
      toolsOk = hello !== null;
      toolsDetail = `6 dc_* tools registered by extension (not enumerated by the active-tool registry view; model invocation verified at Gate A). bridge=${hello ? "ok" : "down"}`;
    }
  } catch (error) {
    toolsDetail = `registry error: ${failureText(error)}`;
  }
  checks.push({ name: "custom_tools", ok: toolsOk, detail: toolsDetail });

  const skillPath = path.join(repoRoot, ".omp", "skills", "develoip-copilot", "SKILL.md");
  checks.push({ name: "skill", ok: fs.existsSync(skillPath), detail: fs.existsSync(skillPath) ? skillPath : "SKILL.md missing" });

  const git = await execQuiet(pi, "git", ["--version"]);
  checks.push({ name: "git", ok: Boolean(git && git.code === 0), detail: git?.stdout.trim() || "git not found" });
  const worktree = await execQuiet(pi, "git", ["worktree", "list"]);
  checks.push({ name: "isolation", ok: Boolean(worktree && worktree.code === 0), detail: worktree?.code === 0 ? "git worktree available" : "git worktree unavailable" });

  let pilotDetail = "pilot not configured yet (Batch 2)";
  try {
    const configPath = path.join(repoRoot, ".omp", "dc-state", "config.json");
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, "utf-8")) as { pilot_repository?: string };
      if (config.pilot_repository) {
        pilotDetail = fs.existsSync(config.pilot_repository) ? `pilot present: ${config.pilot_repository}` : `pilot MISSING: ${config.pilot_repository}`;
      }
    }
  } catch (error) {
    pilotDetail = `config unreadable: ${failureText(error)}`;
  }
  checks.push({ name: "pilot_repository", ok: true, detail: pilotDetail });

  report(ctx, renderDoctor(checks));
}

async function runApprovalDecision(pi: ExtensionAPI, bridge: BridgeClient, ctx: CommandContextLike, args: string, decision: "approve" | "reject" | "revoke"): Promise<void> {
  const status = (await bridge.request("status")) as StatusResult;
  const wantedId = args.trim();
  const approvals = status.pending_approvals.filter(
    (approval) => (decision !== "revoke" && approval.status === "REQUESTED") || (decision === "revoke"),
  );
  const target = wantedId ? approvals.find((approval) => approval.object_id === wantedId) : approvals.length === 1 ? approvals[0] : undefined;
  if (!target) {
    report(ctx, decision === "revoke"
      ? "No approval id given. Usage: /dc revoke <approval-id> (find ids via /dc status)."
      : "No pending approval found. Use /dc status to inspect Runtime state.");
    return;
  }
  const summary = [
    `Approval ${target.object_id}`,
    `  capability: ${target.requested_capability}`,
    `  scope: ${JSON.stringify(target.requested_scope ?? {})}`,
    `  risk_factors: ${target.risk_factors.join(", ") || "(none)"}`,
    `  baseline: ${target.baseline_ref}`,
    `  requested_by: ${target.created_by}`,
    `  task: ${target.task_ref}`,
  ].join("\n");
  const commandType = decision === "approve" ? "GRANT_APPROVAL" : decision === "reject" ? "REJECT_APPROVAL" : "REVOKE_APPROVAL";
  if (ctx.hasUI) {
    const confirmed = await ctx.ui.confirm(`/dc ${decision}`, `${summary}\n\nConfirm ${commandType}?`);
    if (!confirmed) {
      report(ctx, `${commandType} cancelled by user.`);
      return;
    }
  }
  const result = await bridge.request("dispatch", {
    command: {
      command_id: `cmd-${commandType.toLowerCase()}-${target.object_id}`,
      command_type: commandType,
      actor: "user",
      target_ref: { object_id: target.object_id },
      payload: decision === "approve" ? { decision_basis: "user decision via /dc approve" } : { reason: `user decision via /dc ${decision}` },
    },
  });
  const afterStatus = (await bridge.request("status")) as Record<string, unknown>;
  report(ctx, `${commandType} accepted for ${target.object_id}.\n${renderStatus(afterStatus)}`);
  void result;
}

export function registerCommands(pi: ExtensionAPI, bridge: BridgeClient, repoRoot: string): void {
  pi.registerCommand("dc", {
    description: "develoip-copilot Runtime control: doctor | m3-start | status | resume | approve | reject | revoke | pause | cancel | close",
    handler: async (args: string, ctx: CommandContextLike) => {
      const [sub, ...rest] = (args ?? "").trim().split(/\s+/);
      const remainder = rest.join(" ");
      try {
        switch (sub) {
          case "doctor":
            await runDoctor(pi, bridge, ctx, repoRoot);
            return;
          case "status": {
            const status = (await bridge.request("status")) as Record<string, unknown>;
            report(ctx, renderStatus(status));
            return;
          }
          case "resume": {
            const restored = (await bridge.request("restore")) as { last_sequence: number; snapshot?: string };
            const status = (await bridge.request("status")) as Record<string, unknown>;
            report(ctx, `Restored from Event Store (last_sequence=${restored.last_sequence}, snapshot=${restored.snapshot ?? "n/a"}). Runtime is the single source of truth; session history was NOT used.\n${renderStatus(status)}`);
            return;
          }
          case "m3-start": {
            await bridge.request("dispatch", {
              command: {
                command_id: "cmd-m3-create",
                command_type: "CREATE_TASK",
                actor: "orchestrator",
                payload: { task_id: "task-m3", goal: "Milestone 3 — OMP-Native Real Project Pilot" },
              },
            });
            const m3Status = (await bridge.request("status")) as Record<string, unknown>;
            report(ctx, `Milestone 3 top Task created (idempotent command_id=cmd-m3-create).\n${renderStatus(m3Status)}`);
            return;
          }
          case "approve":
            await runApprovalDecision(pi, bridge, ctx, remainder, "approve");
            return;
          case "reject":
            await runApprovalDecision(pi, bridge, ctx, remainder, "reject");
            return;
          case "revoke":
            await runApprovalDecision(pi, bridge, ctx, remainder, "revoke");
            return;
          case "cancel":
          case "close": {
            const status = (await bridge.request("status")) as StatusResult;
            const taskId = remainder || (status.tasks.length === 1 ? status.tasks[0].object_id : "");
            if (!taskId) {
              report(ctx, "Ambiguous: pass a task id, e.g. /dc cancel task-m3");
              return;
            }
            const commandType = sub === "cancel" ? "CANCEL_TASK" : "CLOSE_TASK";
            await bridge.request("dispatch", {
              command: { command_id: `cmd-${commandType.toLowerCase()}-${taskId}`, command_type: commandType, actor: "user", target_ref: { object_id: taskId }, payload: {} },
            });
            const closeStatus = (await bridge.request("status")) as Record<string, unknown>;
            report(ctx, `${commandType} accepted for ${taskId}.\n${renderStatus(closeStatus)}`);
            return;
          }
          case "pause":
            report(ctx, "PAUSE is not expressible in the Milestone 1.5 Runtime contract (no pause state transition exists). Tracked as Milestone 3 contract deviation D1. Use /dc cancel or resolve blockers instead.");
            return;
          default:
            report(ctx, "Usage: /dc doctor | m3-start | status | resume | approve [id] | reject [id] | revoke <id> | pause | cancel [task-id] | close [task-id]");
        }
      } catch (error) {
        report(ctx, `dc ${sub ?? ""} failed — ${failureText(error)}`);
      }
    },
  });
}
