# Milestone 1 架构冻结决议

## 冻结对象

`develoip-copilot` 整体架构设计蓝图 v1.2。

## 冻结状态

```text
Milestone 1 — FROZEN
```

## 冻结结论

v1.2 已完成以下核心闭环：

```text
Task Classification
→ Execution Mode
→ Runtime State
→ Authorization
→ Agent Execution
→ Artifact
→ Evidence
→ Claim
→ Acceptance
→ Closure Gate
→ Persistent Record
```

该架构已经具备：

- 可实现性；
- 可测试性；
- 失败恢复能力；
- 跨会话恢复能力；
- 权限和风险治理能力；
- 工程证据与关闭门禁；
- 后续 OMP/pi 运行时适配空间。

## 正式冻结内容

1. 顶层编排 Agent、专业 Subagent、Skill、Tool 的职责边界。
2. Control Plane、Evidence Plane、Knowledge Plane 三平面架构。
3. DIRECT、ROUTED、ORCHESTRATED 三种执行模式。
4. Task Kind、Domain、Risk Factor、Required Capability 分类维度。
5. 风险增加触发执行模式、权限、验证和关闭门禁重新评估。
6. Execution、Acceptance、Closure 三轴状态模型。
7. Runtime 与 Task Record 的权威和同步关系。
8. Blocker 与失败恢复模型。
9. Artifact、Evidence、Claim、Acceptance、Closure Gate 链路。
10. Baseline 绑定和证据失效传播。
11. 风险分级权限与独立验证原则。
12. Handoff 与 Handoff Acceptance 的分离。
13. Closure Gate 模型。
14. 共享工作区与并发语义。
15. 仓库原生项目发展记录系统。
16. 默认不读、默认不写的克制上下文策略。
17. 平台中立接口语义。
18. QSPI Bug 调查与修复纵向样板方向。

## 冻结后的变更规则

后续不得因实现便利而直接修改上述架构语义。

只有纵向样板证明以下任一情况成立，才允许提出架构变更：

- 核心对象无法表达真实任务；
- 职责边界造成不可消除的循环依赖；
- 状态或权限模型无法阻止错误执行；
- Evidence 与 Claim 无法支持可信关闭；
- OMP/pi 无法映射平台中立接口；
- 项目记录模型造成不可接受的上下文或维护成本。

字段名称、文件格式、目录、Schema 和平台配置变化不属于架构变更。

## 下一里程碑

```text
Milestone 1.5 — Unified Execution Contract
```

唯一正式入口：

```text
execution-contract.md
```

该契约应覆盖：

1. 对象定义；
2. 事件定义；
3. 三轴状态与迁移；
4. 前置条件和后置条件；
5. 权限与审批；
6. Risk Policy Matrix；
7. Artifact–Evidence–Claim 关系；
8. Handoff 与 Acceptance；
9. Blocker 和失败恢复；
10. Closure Gate；
11. Runtime 持久化；
12. 核心不变量；
13. 拒绝规则；
14. 最小契约测试。

Milestone 1.5 不再讨论是否增加角色、平面或记录类型，只负责把已冻结架构转换为最小、统一、可测试的执行契约。
