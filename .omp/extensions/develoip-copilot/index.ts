// develoip-copilot OMP Extension — entry point.
// Registration only; no runtime actions during load. All authority stays in
// the Python Runtime reached through the bridge subprocess.
import * as path from "node:path";
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { BridgeClient } from "./bridge";
import { registerCommands } from "./commands";
import { registerGuard } from "./guards";
import { registerSession } from "./session";
import { registerTools } from "./tools";

export default function develoipCopilot(pi: ExtensionAPI): void {
  const repoRoot = process.cwd();
  const stateDir = path.join(repoRoot, ".omp", "dc-state");
  const bridge = new BridgeClient(repoRoot, stateDir);

  pi.setLabel("develoip-copilot");
  registerGuard(pi, bridge);
  registerTools(pi, bridge);
  registerCommands(pi, bridge, repoRoot);
  registerSession(pi, bridge);
}
