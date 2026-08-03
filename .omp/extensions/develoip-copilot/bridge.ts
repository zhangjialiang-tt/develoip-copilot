// Bridge client: owns the Python bridge subprocess and the JSONL protocol.
// The extension caches ONLY this connection; all authoritative state lives in
// the Python Runtime and is re-queried via request() on every use.
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";

const DEFAULT_TIMEOUT_MS = 30_000;

export class BridgeError extends Error {
  code: string;
  details: Record<string, unknown>;

  constructor(code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.code = code;
    this.details = details;
  }
}

interface Pending {
  resolve: (value: unknown) => void;
  reject: (error: Error) => void;
  timer: ReturnType<typeof setTimeout>;
}

export class BridgeClient {
  private proc: ChildProcessWithoutNullStreams | null = null;
  private pending = new Map<string, Pending>();
  private buffer = "";
  private seq = 0;
  private readonly stderrLog: string;

  constructor(
    private readonly repoRoot: string,
    private readonly stateDir: string,
    private readonly python: string = process.env.DC_PYTHON ?? "python",
  ) {
    this.stderrLog = path.join(stateDir, "bridge.stderr.log");
  }

  get isRunning(): boolean {
    return this.proc !== null;
  }

  async ensureStarted(): Promise<void> {
    if (this.proc) return;
    this.buffer = ""; // drop any partial frame from a previous process
    fs.mkdirSync(this.stateDir, { recursive: true });
    const proc = spawn(
      this.python,
      ["-m", "runtime.omp_bridge", "--stdio", "--state-dir", this.stateDir],
      {
        cwd: this.repoRoot,
        stdio: ["pipe", "pipe", "pipe"],
        // The JSONL protocol is UTF-8; force it in the child regardless of the
        // Windows locale code page (GBK would corrupt non-ASCII payloads).
        env: { ...process.env, PYTHONIOENCODING: "utf-8", PYTHONUTF8: "1" },
      },
    ) as ChildProcessWithoutNullStreams;

    proc.stdout.setEncoding("utf-8");
    proc.stdout.on("data", (chunk: string) => this.onData(chunk));
    proc.stderr.setEncoding("utf-8");
    proc.stderr.on("data", (chunk: string) => {
      try {
        fs.appendFileSync(this.stderrLog, chunk);
      } catch {
        // stderr logging must never break the bridge pipe
      }
    });
    proc.on("exit", (code) => {
      if (this.proc !== proc) return; // a restarted bridge already replaced this one
      this.proc = null;
      const error = new BridgeError("BRIDGE_DOWN", `Python bridge exited (code=${code}); state persists in the event store and restores on next request`);
      for (const [id, waiter] of this.pending) {
        clearTimeout(waiter.timer);
        waiter.reject(error);
        this.pending.delete(id);
      }
    });
    proc.on("error", (spawnError) => {
      if (this.proc !== proc) return;
      this.proc = null;
      const failure = new BridgeError("BRIDGE_SPAWN_FAILED", `Cannot start Python bridge: ${spawnError.message}`);
      for (const [id, waiter] of this.pending) {
        clearTimeout(waiter.timer);
        waiter.reject(failure);
        this.pending.delete(id);
      }
    });
    this.proc = proc;
  }

  async request(op: string, params: Record<string, unknown> = {}, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<any> {
    await this.ensureStarted();
    const proc = this.proc;
    if (!proc || !proc.stdin.writable) {
      throw new BridgeError("BRIDGE_DOWN", "Python bridge is not running");
    }
    const id = `omp-${++this.seq}`;
    const frame = JSON.stringify({ id, op, params });
    return await new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new BridgeError("BRIDGE_TIMEOUT", `Bridge op '${op}' timed out after ${timeoutMs}ms`));
      }, timeoutMs);
      this.pending.set(id, {
        timer,
        resolve: (value) => resolve(value),
        reject: (error) => reject(error),
      });
      proc.stdin.write(frame + "\n");
    });
  }

  async health(): Promise<{ ok: boolean; detail: string }> {
    try {
      const result = await this.request("health", {}, 5_000);
      return { ok: true, detail: `bridge pid=${result.pid} last_sequence=${result.last_sequence}` };
    } catch (error) {
      return { ok: false, detail: error instanceof Error ? error.message : String(error) };
    }
  }

  stop(): void {
    if (!this.proc) return;
    const proc = this.proc;
    this.proc = null;
    try {
      proc.stdin.end();
    } catch {
      // already closed
    }
    proc.kill();
  }

  private onData(chunk: string): void {
    this.buffer += chunk;
    let newline = this.buffer.indexOf("\n");
    while (newline !== -1) {
      const line = this.buffer.slice(0, newline).trim();
      this.buffer = this.buffer.slice(newline + 1);
      newline = this.buffer.indexOf("\n");
      if (!line) continue;
      let frame: any;
      try {
        frame = JSON.parse(line);
      } catch {
        continue;
      }
      const waiter = frame?.id ? this.pending.get(frame.id) : undefined;
      if (!waiter) continue;
      this.pending.delete(frame.id);
      clearTimeout(waiter.timer);
      if (frame.ok) {
        waiter.resolve(frame.result);
      } else {
        const error = frame.error ?? {};
        waiter.reject(new BridgeError(error.code ?? "BRIDGE_ERROR", error.message ?? "Unknown bridge error", error.details ?? {}));
      }
    }
  }
}
