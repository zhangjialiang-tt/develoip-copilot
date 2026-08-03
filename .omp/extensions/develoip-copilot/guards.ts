// Tool Guard: programmatic WRITE gate for edit/write/ast_edit/bash.
// The decision always comes from the Python Runtime (guard_check); prompt-level
// "please do not modify files" is never sufficient. Fail-closed when the bridge
// is unreachable.
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import type { BridgeClient } from "./bridge";

const GUARDED_TOOLS: Record<string, true> = { edit: true, write: true, ast_edit: true, bash: true };
const EDIT_SECTION = /\[([^\]#]+)#[0-9a-fA-F]{4}\]/g;

interface GuardTargets {
  paths: string[];
  command?: string;
  cwd?: string;
}

interface ToolCallEventLike {
  toolName: string;
  input: Record<string, unknown>;
}

interface GuardDecision {
  allowed: boolean;
  code?: string;
  reason?: string;
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function extractTargets(toolName: string, input: Record<string, unknown>): GuardTargets {
  const paths: string[] = [];
  if (toolName === "write") {
    const path = asString(input.path);
    if (path) paths.push(path);
  }
  if (toolName === "ast_edit" && Array.isArray(input.paths)) {
    for (const entry of input.paths) {
      if (typeof entry === "string") paths.push(entry);
    }
  }
  if (toolName === "edit") {
    const body = asString(input.input) ?? "";
    for (const match of body.matchAll(EDIT_SECTION)) paths.push(match[1]);
  }
  if (toolName === "bash") {
    return { paths, command: asString(input.command) ?? "", cwd: asString(input.cwd) };
  }
  return { paths };
}

export function registerGuard(pi: ExtensionAPI, bridge: BridgeClient): void {
  pi.on("tool_call", async (event: ToolCallEventLike) => {
    if (!GUARDED_TOOLS[event.toolName]) return;
    const { paths, command, cwd } = extractTargets(event.toolName, event.input ?? {});
    let decision: GuardDecision;
    try {
      decision = (await bridge.request("guard_check", { tool_name: event.toolName, paths, command, cwd }, 10_000)) as GuardDecision;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return { block: true, reason: `[dc-guard] bridge unavailable (${message}); WRITE is fail-closed. Use /dc doctor.` };
    }
    if (!decision.allowed) {
      return { block: true, reason: `[dc-guard] ${decision.code}: ${decision.reason}. Obtain a Runtime WRITE Approval via /dc approve or adjust the scope.` };
    }
  });
}
