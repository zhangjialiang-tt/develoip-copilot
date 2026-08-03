// Rendering helpers: turn Runtime query results into plain-text reports.
// All values come from dc_query/status results; nothing here recomputes state.

type AnyRecord = Record<string, unknown>;

export function renderStatus(status: AnyRecord): string {
  const lines: string[] = [];
  lines.push(`Event sequence: ${status.last_sequence}`);
  const tasks: AnyRecord[] = status.tasks ?? [];
  if (tasks.length === 0) {
    lines.push("Tasks: (none) — use /dc m3-start to create the Milestone 3 task");
  }
  for (const task of tasks) {
    lines.push("");
    lines.push(`Task ${task.object_id} [${task.execution_status}] closure=${task.closure_status}`);
    lines.push(`  goal: ${task.goal ?? ""}`);
    lines.push(`  baseline: ${task.baseline_ref ?? "(unbound)"}  capabilities: ${(task.required_capabilities ?? []).join(",") || "(none)"}`);
    const gates: AnyRecord[] = task.gates ?? [];
    for (const gate of gates) {
      lines.push(`  gate ${gate.gate_type}: ${gate.status}${gate.required ? "" : " (optional)"}`);
    }
    const actions: string[] = status.next_legal_actions?.[task.object_id] ?? [];
    if (actions.length > 0) lines.push(`  next legal actions: ${actions.join(" | ")}`);
  }
  const approvals: AnyRecord[] = status.pending_approvals ?? [];
  if (approvals.length > 0) {
    lines.push("");
    lines.push("Awaiting user decision:");
    for (const approval of approvals) {
      lines.push(`  ${approval.object_id}: capability=${approval.requested_capability} scope=${JSON.stringify(approval.requested_scope ?? {})} baseline=${approval.baseline_ref} risk=${(approval.risk_factors ?? []).join(",") || "(none)"}`);
    }
  }
  const blockers: AnyRecord[] = status.active_blockers ?? [];
  if (blockers.length > 0) {
    lines.push("");
    lines.push("Active blockers:");
    for (const blocker of blockers) {
      lines.push(`  ${blocker.object_id} [${blocker.blocker_type}] ${blocker.description ?? ""}`);
    }
  }
  return lines.join("\n");
}

export function renderDoctor(checks: { name: string; ok: boolean; detail: string }[]): string {
  const lines = ["/dc doctor"];
  for (const check of checks) {
    lines.push(`${check.ok ? "[PASS]" : "[FAIL]"} ${check.name}: ${check.detail}`);
  }
  const failed = checks.filter((check) => !check.ok);
  lines.push(failed.length === 0 ? "RESULT: PASS" : `RESULT: FAIL (${failed.length} check(s) failed)`);
  return lines.join("\n");
}
