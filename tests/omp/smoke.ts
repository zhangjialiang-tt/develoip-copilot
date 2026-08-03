// Bun smoke test for the OMP extension (Gate A support):
// 1) extension factory loads and registers guard/tools/command/renderer;
// 2) the TS BridgeClient drives a REAL python bridge subprocess end-to-end.
import { plugin } from "bun";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

// Virtual modules: OMP packages are host-provided at runtime; shim them here.
plugin({
  name: "omp-shims",
  setup(build) {
    build.module("@oh-my-pi/pi-tui", () => ({
      contents:
        "export class Container { addChild(): void {} } export class Text { constructor(public text?: string) {} }",
      loader: "ts",
    }));
    build.module("@oh-my-pi/pi-coding-agent", () => ({
      contents: "export type ExtensionAPI = never;",
      loader: "ts",
    }));
  },
});

let failures = 0;

function check(name: string, ok: boolean, detail = ""): void {
  console.log(`${ok ? "[PASS]" : "[FAIL]"} ${name}${detail ? `: ${detail}` : ""}`);
  if (!ok) failures += 1;
}

// ---- 1) factory registration -------------------------------------------
const schemaStub = (): Record<string, unknown> => ({ optional: () => schemaStub(), describe: () => schemaStub() });
const zodStub = {
  object: (_shape?: unknown) => schemaStub(),
  string: () => schemaStub(),
  boolean: () => schemaStub(),
  unknown: () => schemaStub(),
  array: (_inner?: unknown) => schemaStub(),
  record: (_k?: unknown, _v?: unknown) => schemaStub(),
  enum: (_values?: unknown) => schemaStub(),
};

const registeredTools: string[] = [];
const registeredCommands: string[] = [];
const registeredHandlers: string[] = [];
const registeredRenderers: string[] = [];

const piMock = {
  zod: { z: zodStub },
  setLabel: (_label: string) => {},
  on: (event: string, _handler: unknown) => {
    registeredHandlers.push(event);
  },
  registerTool: (definition: { name: string }) => {
    registeredTools.push(definition.name);
  },
  registerCommand: (name: string, _definition: unknown) => {
    registeredCommands.push(name);
  },
  registerMessageRenderer: (customType: string, _renderer: unknown) => {
    registeredRenderers.push(customType);
  },
  appendEntry: (_type: string, _data: unknown) => {},
  exec: async () => ({ code: 0, stdout: "", stderr: "" }),
  getAllTools: () => [],
};

const { default: factory } = await import("../../.omp/extensions/develoip-copilot/index.ts");
factory(piMock);

check("guard handler registered", registeredHandlers.includes("tool_call"), registeredHandlers.join(","));
check("session lifecycle handlers registered", registeredHandlers.includes("session_start") && registeredHandlers.includes("session_shutdown"));
check("dc tools registered", ["dc_dispatch", "dc_query", "dc_restore", "dc_invoke_role", "dc_submit_candidates", "dc_workspace_status"].every((name) => registeredTools.includes(name)), registeredTools.sort().join(","));
check("dc command registered", registeredCommands.includes("dc"), registeredCommands.join(","));

// ---- 2) TS client against real python bridge ---------------------------
const { BridgeClient } = await import("../../.omp/extensions/develoip-copilot/bridge.ts");
const repoRoot = path.resolve(import.meta.dir, "..", "..");
const stateDir = fs.mkdtempSync(path.join(os.tmpdir(), "dc-smoke-"));
const bridge = new BridgeClient(repoRoot, stateDir);

try {
  const hello = (await bridge.request("hello")) as { protocol_version: number; last_sequence: number };
  check("bridge hello", hello.protocol_version === 1, `protocol v${hello.protocol_version}`);

  await bridge.request("dispatch", {
    command: { command_id: "cmd-smoke-create", command_type: "CREATE_TASK", actor: "orchestrator", payload: { task_id: "task-smoke", goal: "smoke — 中文" } },
  });
  const status = (await bridge.request("status")) as { tasks: { object_id: string }[] };
  check("dispatch CREATE_TASK + status", status.tasks.some((task) => task.object_id === "task-smoke"));

  const allowed = (await bridge.request("guard_check", { tool_name: "write", paths: ["unrelated/x.txt"] })) as { allowed: boolean; reason: string };
  check("guard allows ungoverned write", allowed.allowed === true, allowed.reason);

  const error = await bridge.request("dispatch", { command: { command_id: "cmd-smoke-bad", command_type: "SET_GATE_STATUS", actor: "orchestrator", payload: {} } }).then(
    () => null,
    (failure: { code?: string }) => failure,
  );
  check("derived write rejected", error?.code === "DERIVED_RESULT_WRITE_FORBIDDEN");

  // Bridge crash/stop recovery: after the process is torn down the client must
  // restart it on next request and recover state via event-store replay.
  bridge.stop();
  const helloAgain = (await bridge.request("hello")) as { protocol_version: number };
  check("bridge restarts after stop", helloAgain.protocol_version === 1);
  const statusAgain = (await bridge.request("status")) as { tasks: { object_id: string }[] };
  check("state recovered after restart", statusAgain.tasks.some((task) => task.object_id === "task-smoke"));
} finally {
  bridge.stop();
  fs.rmSync(stateDir, { recursive: true, force: true });
}

console.log(failures === 0 ? "SMOKE PASS" : `SMOKE FAIL (${failures})`);
process.exit(failures === 0 ? 0 : 1);
