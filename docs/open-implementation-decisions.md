# Open Implementation Decisions

> 本文件是 [execution-contract.md](execution-contract.md) 的实现期决策清单，不是契约补充规范。它记录“如何实现”，不改变对象、状态、Command、Event、Derived Result 或 Gate 语义。
> 这些事项不阻止 Milestone 1.5 冻结；进入 Milestone 2 时逐项决策并用实现测试闭环。

## OI-01 — Runtime Event 存储介质

- **开放内容**：事件日志采用文件、嵌入式数据库或现有 Runtime 存储接口。
- **必须保持**：`RuntimeEvent` 不可变；`command_id` 幂等；`sequence` 可校验；事件可按 Task/aggregate 恢复。
- **决策时机**：Milestone 2 Runtime 设计。
- **验收证据**：重复 Command、断点恢复、事件序列冲突三类测试。

## OI-02 — Snapshot 与增量事件策略

- **开放内容**：快照频率、快照大小和需要回放的事件窗口。
- **必须保持**：快照不是第二事实源；快照与事件冲突时进入 `CONTRACT_FAILURE`/`BLOCKED`，不得静默选择某一侧。
- **决策时机**：首次实现跨会话 Restore 前。
- **验收证据**：从快照恢复 Derived Result 与完整回放结果一致。

## OI-03 — 物理 Schema 和 ID 编码

- **开放内容**：JSON、YAML、数据库记录或平台 API 的字段编码、时间格式和引用序列化。
- **必须保持**：稳定唯一 ID、显式对象类型、引用不复制状态、枚举值与本契约一致。
- **决策时机**：Milestone 2 最小物理 Schema。
- **验收证据**：schema round-trip、未知字段处理和非法枚举拒绝测试。

## OI-04 — Scope 冲突检测

- **开放内容**：文件级、模块级、接口级和设备级 Scope 的重叠判断算法。
- **必须保持**：同一受控 Scope 不能被两个写角色并发修改；用户未提交修改受保护；冲突不得静默合并。
- **决策时机**：首个 WRITE Tool 接入前。
- **验收证据**：同 Scope、相交 Scope、无关 Scope 和用户未提交变更四类并发测试。

## OI-05 — Baseline 捕获和比较实现

- **开放内容**：commit、工作区快照、配置、工具版本和输入数据的哈希/引用策略。
- **必须保持**：Baseline 能回答“哪个实现、哪些配置、哪些工具、哪些输入”；变化触发失效传播和 Approval 重评估。
- **决策时机**：首个验证 Artifact 注册前。
- **验收证据**：代码、配置、输入、工具任一变化都能被识别并使相关 Evidence 重新评估。

## OI-06 — Evidence coverage 和 relevance 的领域判据

- **开放内容**：QSPI 协议、边界、顺序、错误路径和跨模块覆盖如何由 Verification Tool 计算或由 Reviewer 确认。
- **必须保持**：coverage、relevance、reproducibility 和 independence 分开表达；E3 不能自动满足 Gate。
- **决策时机**：QSPI Vertical Slice Test Design。
- **验收证据**：同为 E3 但覆盖不足的 Evidence 不能关闭 protocol Gate。

## OI-07 — Approval 交互适配

- **开放内容**：用户授权是 CLI、UI、API 还是平台原生确认。
- **必须保持**：授权必须明确目标、Scope、Capability、Risk、Baseline 和保留门禁；支持拒绝、撤销和失效。
- **决策时机**：首个 WRITE/EXTERNAL_DEVICE_ACCESS Tool 接入前。
- **验收证据**：范围扩大、Risk 新增、Baseline 变化和撤销都能阻止越权继续。

## OI-08 — Validator 调度和结果回传

- **开放内容**：Verification Engineer、Integration Reviewer 和外部板级 Validator 的调用协议。
- **必须保持**：Validator 角色与实现角色可区分；失败结果形成 Evidence/Blocker，不被实现者自测覆盖。
- **决策时机**：Milestone 2 首个 QSPI 验证链路。
- **验收证据**：验证失败、工具失败和环境失败映射到不同 Blocker/恢复路径。

## OI-09 — Record Gate 的候选判定

- **开放内容**：哪些 Task/Claim/Evidence 变化达到长期 Record 候选门槛，以及 Record 的仓库原生落点。
- **必须保持**：运行恢复必需持久化不依赖用户是否愿意写长期 Record；用户拒绝只解决 record_gate，不创造技术 Acceptance。
- **决策时机**：Knowledge/Record 适配阶段。
- **验收证据**：用户拒绝、Documenter 判定无需记录、写入并写后验证三条路径均可结束 record_gate。

## OI-10 — Runtime 与平台适配接口

- **开放内容**：OMP/pi 或其他平台如何映射 Command、Event、Handoff 和 Restore。
- **必须保持**：平台适配不改变平台中立契约；不得暴露 Derived Result 直接写入口；Runtime/Task Record 不双写。
- **决策时机**：Milestone 2 OMP/pi 原型适配。
- **验收证据**：平台调用与本契约场景 S03、S06、S13、S20、S24 结果一致。

## OI-11 — QSPI 板级动作的回滚策略

- **开放内容**：硬件状态变化的设备命令、操作窗口、回滚和人工确认方式。
- **必须保持**：`HARDWARE_STATE_CHANGE` 使用 `EXTERNAL_DEVICE_ACCESS`；需要 User/board validator 和 `EXTERNAL_SOURCE`；不能由本机日志伪造外部独立性。
- **决策时机**：板级验证 Tool 设计前。
- **验收证据**：未授权设备动作被拒绝；设备异常进入正确 Blocker；回滚条件可验证。

## OI-12 — 实现期命令错误码集合

- **开放内容**：平台 API 的具体错误码、用户提示和重试语义。
- **必须保持**：每次拒绝都能表达缺少的前置条件、受影响对象和恢复建议；拒绝不产生部分成功事实。
- **决策时机**：首个可调用 Runtime API 前。
- **验收证据**：所有核心拒绝场景至少有稳定的机器可识别错误类别。

## Freeze boundary

这些事项可以选择不同实现，但不得借实现选择改变以下冻结事实：

```text
Task/Subtask unified
Command is the only write entry
Domain Event is immutable
Derived Result is computed
Risk increases trigger re-evaluation
Acceptance and Waiver are separate
Baseline invalidation propagates
Handoff acceptance is not technical acceptance
Closure depends on Gates
Runtime and Task Record do not double-write
Project Status is a read-only projection
```
