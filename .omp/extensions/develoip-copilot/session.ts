// Session lifecycle: use events to check bridge health and persist snapshots.
// Session history is NEVER used to reconstruct authoritative state — recovery
// always replays the Event Store via /dc resume or dc_restore.
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import type { BridgeClient } from "./bridge";

export function registerSession(pi: ExtensionAPI, bridge: BridgeClient): void {
  pi.on("session_start", async () => {
    try {
      await bridge.ensureStarted();
      await bridge.request("health", {}, 5_000);
    } catch {
      // Health failures surface through /dc doctor and the tool guard;
      // session start must not crash on them.
    }
  });

  pi.on("session_shutdown", async () => {
    try {
      if (bridge.isRunning) {
        await bridge.request("save_snapshot", {}, 5_000);
      }
    } catch {
      // Snapshot is an optimization; the Event Store remains authoritative.
    } finally {
      bridge.stop();
    }
  });
}
