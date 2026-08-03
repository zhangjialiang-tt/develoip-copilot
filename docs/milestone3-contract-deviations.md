# Milestone 3 — 契约偏差记录（milestone3-contract-deviations）

> 记录 Milestone 3 实施中与 `docs/execution-contract.md`（Milestone 1.5 冻结契约）不一致的行为。
> 无偏差的方面明确声明：截至本文件更新时，除下列条目外 No known contract deviations。

## D1 — `/dc pause` 无契约支撑（OPEN）

- 计划 §8.5 要求最小命令集包含 `/dc pause`。
- M1.5 契约的 Task Execution Status 迁移中没有暂停/恢复状态；Runtime 无法表达 pause。
- 处理：命令已注册，执行时回报"契约不支持"并指向替代路径（解决 Blocker 或 cancel）。
- 影响：不削弱任何安全门禁；属命令面缺口，不属状态权威分裂。
- 关闭条件：契约后续版本引入暂停语义，或计划正式撤回该命令。

## 非偏差的调整（计划明确允许，仅存档）

1. 物理目录：Extension 源码位于 `.omp/extensions/develoip-copilot/`（计划 §20 允许 Batch 1 调整目录，职责边界未变）。
2. Custom Tool 由 Extension `registerTool` 注册（计划 §8.4 允许"注册或装配"二选一；选择单一加载路径以满足 §8.2"不得同时维护多套加载路径"）。
3. Bridge op 集相对计划 §8.3"最小操作"新增 `status` / `submit_candidates` / `guard_check`：均为只读查询或协议转换，不引入第二状态源，不改变 Runtime 单一写入口。
4. `runtime/roles.py` 禁止字段集合扩展 `approval_granted` / `task_closed`：与计划 §10 角色输出协议对齐，属契约加强而非放宽；M2 既有测试不受影响。
