# develoip-copilot Milestone 2 执行计划

> 里程碑名称：QSPI Vertical Slice Implementation
> 前置基线：Milestone 1.5 — `EXECUTED / FROZEN`
> 开发分支：`base/develop`
> 计划状态：`EXECUTED / FROZEN`
> 核心目标：将冻结的执行契约实现为一条最小、真实、可运行、可恢复的 QSPI 工程闭环
> 权威契约：`docs/execution-contract.md`

---

# 1. 里程碑目标

Milestone 2 不建设完整的 FPGA 工程 Agent 平台。

本阶段只实现一条最小纵向链路：

```text
Task 创建与分类
→ Baseline 捕获
→ System Investigator 调查
→ Evidence / Claim 注册
→ Verification Engineer 建立复现
→ Risk 升级
→ WRITE Approval
→ RTL Engineer 修改受控样板
→ 独立验证
→ Integration Reviewer 接受
→ Closure Gate 计算
→ Runtime 持久化与恢复
→ 工程记录处置
```

通过这条链路验证：

1. `execution-contract.md` 可以被代码实现；
2. 24 个契约场景可以转化为自动化测试；
3. Agent、Skill、Tool、Runtime 的职责边界能够落地；
4. QSPI Bug 调查和修复不依赖完整聊天历史；
5. OMP/pi 可以通过适配层调用运行时，而不改变平台中立契约；
6. 项目记录系统不会退化为每轮自动读写的日志系统。

---

# 2. Milestone 2 成功定义

Milestone 2 完成时，系统至少能够：

- 创建、分类和恢复一个 Task；
- 拒绝非法 Command；
- 产生不可变 Domain Event；
- 从对象和事件计算 Derived Result；
- 捕获并比较 Baseline；
- 处理 Approval 授予、撤销和失效；
- 注册 Artifact、Evidence 和 Claim；
- 传播 Baseline 变化导致的失效；
- 创建并接收 Handoff；
- 区分 Handoff Acceptance、技术 Acceptance 和 Waiver；
- 创建和解除 Blocker；
- 计算 Closure Gate；
- 在进程重启后恢复 Task；
- 完成一条 QSPI 样板成功路径；
- 完成至少一条验证失败和返工路径；
- 通过 OMP/pi 原型适配层执行关键 Command。

本阶段关闭的是：

```text
QSPI 纵向样板运行能力
```

不是：

```text
真实产品中的全部 QSPI Bug
完整 develoip-copilot 产品
完整 FPGA 开发生命周期
```

---

# 3. 冻结输入

Milestone 2 必须以以下内容为冻结输入：

```text
docs/execution-contract.md
docs/contract-test-scenarios.md
docs/qspi-contract-walkthrough.md
docs/open-implementation-decisions.md
docs/Milestone1架构冻结决议.md
```

开始编码前必须记录：

- `base/develop` 的起始 commit；
- 工作区是否干净；
- Milestone 1.5 文件哈希或 Git 引用；
- 使用的工具链和运行环境。

`execution-contract.md` 在 Milestone 2 中保持唯一语义权威。

实现不得为了方便而改变：

- 核心对象；
- 三轴状态；
- Command 是唯一写入口；
- Domain Event 不可变；
- Derived Result 只能计算；
- Acceptance 与 Waiver 分离；
- Runtime 与 Task Record 不双写；
- Project Status 是只读投影。

发现契约自身存在 P0 缺陷时，必须停止实现并提出 Milestone 1.5 重开申请，不得在代码中静默创造新语义。

---

# 4. 本阶段不做什么

Milestone 2 不包含：

- 完整多项目管理；
- 任意工作流 DSL；
- 用户可配置状态机；
- 通用数据库服务；
- 完整 Web UI；
- 完整 OMP/pi Extension 产品化；
- 多级组织审批；
- 全部 FPGA Risk Policy；
- 任意并行写调度；
- 自动烧写真实板卡；
- 无人值守修改生产工程；
- 全量专业 Subagent；
- 自动提交、推送和创建 PR；
- 完整 Project Status 产品界面。

默认不执行真实板卡状态修改。

如果需要接入板卡，只允许通过单独授权的后续扩展进入，不得把它作为 Milestone 2 冻结的必要条件。

---

# 5. 最小实现组成

Milestone 2 只实现以下六部分。

## 5.1 Contract Runtime Kernel

负责：

- Command 校验；
- Ownership 校验；
- 状态迁移；
- Domain Event 生成；
- Derived Result 计算；
- 幂等处理；
- 对象引用检查；
- 拒绝结果；
- Runtime 恢复。

## 5.2 Persistence Adapter

负责：

- Runtime Event 追加写入；
- Event sequence 校验；
- Task 聚合恢复；
- 最小 Snapshot；
- Runtime 与 Task Record 持久化边界。

首版应优先采用简单、可检查、仓库友好的实现，不建设数据库服务。

推荐默认假设：

```text
Append-only JSONL Event Store
+ 可选 JSON Snapshot
+ 明确 Schema Version
```

最终选择在 Batch 1 通过 ADR 冻结。

## 5.3 Policy and Derived Engine

负责：

- Risk Policy；
- Approval 有效性；
- Baseline 失效传播；
- Claim 支持状态；
- Evidence 有效性；
- Gate 状态；
- Closure Status；
- record gate 处置状态。

这些结果不能提供直接写接口。

## 5.4 Role Invocation Layer

首批只支持纵向样板必需角色：

```text
Top-level Orchestrator
System Investigator
RTL Engineer
Verification Engineer
Integration Reviewer
Engineering Documenter
```

Milestone 2 不要求这些角色全部成为长期运行的独立 Agent 进程。

首版可以通过统一的 Role Invocation Interface 调用：

- 真实 Agent；
- OMP/pi 子代理；
- 测试 Stub；
- 人工外部 Validator。

无论采用哪种调用方式，输入和输出都必须使用相同 Handoff 契约。

## 5.5 Minimal Skills and Tools

只实现 QSPI 样板真正复用的方法和确定性操作。

候选 Skill：

```text
investigation-evidence-chain
qspi-reproduction-design
rtl-change-impact-review
verification-evidence-assessment
engineering-record-distillation
```

每个 Skill 只承担一种稳定方法，不承担端到端任务。

候选 Tool：

```text
baseline-capture
scope-diff
safe-command-runner
artifact-register
evidence-import
test-result-parser
event-store-validator
record-reference-validator
```

## 5.6 QSPI Fixture

建立一个自包含、确定性、可重复的 QSPI 样板工程，至少包括：

- 最小拼接 RTL；
- 已知错误版本；
- 修复版本或可修复点；
- 输入向量；
- 期望输出；
- testbench；
- 自动结果检查；
- 至少一条错误路径；
- Baseline A 与 Baseline B；
- 可用于独立验证的第二种检查方法。

样板不得依赖未授权的真实生产工程。

如果后续使用真实 QSPI 工程，应通过外部 Workspace Adapter 接入，而不是把生产代码复制进 develoip-copilot 仓库。

---

# 6. 实现期开放决策处理

Milestone 2 应对现有开放决策进行分级关闭。

## 6.1 本阶段必须关闭

| 决策                              | Milestone 2 要求               |
| --------------------------------- | ------------------------------ |
| OI-01 Runtime Event 存储          | 选择并实现最小 Event Store     |
| OI-03 物理 Schema 和 ID           | 冻结 runtime v1 Schema         |
| OI-05 Baseline 捕获               | 实现代码、配置、工具和输入识别 |
| OI-06 Evidence coverage/relevance | 冻结 QSPI 样板判据             |
| OI-07 Approval 交互               | 实现至少一种可用确认适配       |
| OI-08 Validator 调度              | 实现验证和审查结果回传         |
| OI-10 平台适配                    | 完成 OMP/pi 原型映射           |
| OI-12 错误码                      | 冻结最小机器可识别拒绝类别     |

## 6.2 本阶段最小关闭

| 决策              | 最小实现                                 |
| ----------------- | ---------------------------------------- |
| OI-02 Snapshot    | 支持一次可验证恢复，不做复杂压缩策略     |
| OI-04 Scope 冲突  | 先实现文件级 Scope；模块和接口级保留扩展 |
| OI-09 Record Gate | 支持写入、拒绝、无需记录三条路径         |

## 6.3 本阶段默认延期

| 决策               | 处理                                         |
| ------------------ | -------------------------------------------- |
| OI-11 板级动作回滚 | 不执行真实设备动作；只支持外部 Evidence 导入 |

如 Milestone 2 决定实际访问板卡，OI-11 必须升级为阻塞项并单独评审。

---

# 7. 执行方式

Milestone 2 采用五个 Batch。

```text
Batch 1：实现基线与 Runtime 骨架
Batch 2：契约内核与自动化测试
Batch 3：角色、Skill、Tool 和适配层
Batch 4：QSPI 纵向闭环
Batch 5：恢复、OMP/pi 验证与冻结
```

每个 Batch 直接更新同一实现，不先建立多套平行原型。

---

# 8. Batch 1：实现基线与 Runtime 骨架

## 8.1 目标

冻结最小技术方案，并建立可执行但尚不完整的 Runtime 骨架。

## 8.2 工作项

### 8.2.1 冻结起始基线

- 记录 `base/develop` 起始 commit；
- 确认工作区干净；
- 建立 Milestone 2 实施分支或明确提交策略；
- 禁止以 `main` 为开发基线。

### 8.2.2 技术选择 ADR

至少决定：

- Runtime 实现语言；
- 类型模型方式；
- Schema 校验方式；
- Event Store 格式；
- Snapshot 方式；
- CLI/进程调用边界；
- OMP/pi 适配边界。

技术选择必须服从契约，不得反向修改契约语义。

### 8.2.3 建立物理对象模型

将 12 个核心对象映射为最小物理 Schema：

```text
Task
Baseline
Approval
Artifact
Evidence
Claim
Handoff
Acceptance
Waiver
Blocker
ClosureGate
RuntimeEvent
```

要求：

- 稳定 ID；
- 显式对象类型；
- Schema version；
- 引用不复制状态；
- 枚举与契约一致；
- 非法枚举拒绝；
- round-trip 不丢字段。

### 8.2.4 建立 Command Dispatcher

至少支持：

```text
CREATE_TASK
CLASSIFY_TASK
BIND_BASELINE
START_TASK
REQUEST_APPROVAL
GRANT_APPROVAL
REJECT_APPROVAL
REVOKE_APPROVAL
INVALIDATE_APPROVAL
REGISTER_ARTIFACT
REGISTER_EVIDENCE
CREATE_CLAIM
LINK_CLAIM_EVIDENCE
SUBMIT_HANDOFF
ACCEPT_HANDOFF
RECORD_ACCEPTANCE
CREATE_WAIVER
CREATE_BLOCKER
RESOLVE_BLOCKER
REQUEST_CLOSURE
CLOSE_TASK
CANCEL_TASK
```

### 8.2.5 Event Store 最小实现

必须支持：

- append-only；
- `command_id` 幂等；
- `event_id` 唯一；
- sequence 连续性检查；
- 按 Task/aggregate 回放；
- 损坏或冲突时拒绝恢复；
- 不静默修复事件。

## 8.3 Gate A：Runtime 骨架门禁

进入 Batch 2 前必须满足：

- 12 个对象可以序列化和反序列化；
- Command 是唯一写入口；
- Domain Event 不可修改；
- Derived Result 没有直接 setter；
- 相同 Command 重试不重复产生事实；
- Event sequence 冲突能被识别；
- Runtime 可创建并恢复最小 Task。

---

# 9. Batch 2：契约内核与自动化测试

## 9.1 目标

把 24 个文档契约场景转化为可执行测试。

采用：

```text
Red
→ Green
→ Refactor
```

不得先实现大而全的 Runtime，再回头补测试。

## 9.2 工作项

### 9.2.1 场景测试转译

每个场景保留：

- Given；
- When；
- Then；
- Reject if；
- Expected events；
- Expected derived results；
- Related invariants。

测试名称必须能够反向定位原始场景编号。

例如：

```text
S03_direct_derived_write_is_rejected
C01_new_protocol_risk_invalidates_old_approval
C08_revoked_write_approval_stops_formal_changes
```

### 9.2.2 状态与 Ownership

实现：

- Execution Status；
- Acceptance；
- Closure；
- Ownership Matrix；
- 合法状态迁移；
- 非法状态迁移拒绝。

### 9.2.3 Approval 和 Risk Policy

先只实现 QSPI 涉及的 Risk：

```text
PROTOCOL_BEHAVIOR_CHANGE
STORAGE_LAYOUT_CHANGE
BASELINE_CHANGE
HARDWARE_STATE_CHANGE
```

如 fixture 涉及其他风险，再按契约增加。

### 9.2.4 Artifact–Evidence–Claim

实现：

- Artifact 注册门槛；
- Evidence validity；
- Reproducibility；
- Relevance；
- Coverage；
- Independence；
- Claim 支持与反证；
- Claim 不可原地升级；
- Baseline 失效传播。

### 9.2.5 Gate 与 Closure

实现 QSPI 样板所需 Gate：

```text
root_cause_gate
implementation_gate
simulation_gate
protocol_gate
integration_gate
risk_acceptance_gate
record_gate
```

不实现任意自定义 Gate。

## 9.3 Gate B：契约一致性门禁

必须满足：

- 24 个契约场景全部自动化；
- 8 个跨模型组合场景全部自动化；
- 所有 Reject 场景不产生部分成功事件；
- S03 类直接修改 Derived Result 被拒绝；
- Baseline 变化使相关 Evidence 和 Gate 重算；
- Approval 撤销后正式写入停止；
- Handoff Acceptance 不改变技术 Acceptance；
- Waiver 不能把错误 Claim 变成正确；
- `FINISHED ≠ ACCEPTED ≠ CLOSED` 在测试中成立。

---

# 10. Batch 3：角色、Skill、Tool 和适配层

## 10.1 目标

建立真实执行边界，而不是让测试直接调用所有内部对象。

## 10.2 Role Invocation Interface

统一输入：

```text
role
task_ref
handoff_ref
scope
approval_refs
baseline_ref
allowed_tools
expected_output
completion_criteria
```

统一输出：

```text
status
artifact_candidates
evidence_candidates
claim_candidates
risk_proposals
blocker_proposals
handoff_candidate
summary
```

专业角色只能提出候选对象。

对象是否正式生效，仍由合法 Runtime Command 决定。

## 10.3 首批角色

### Top-level Orchestrator

负责：

- Task 分类；
- Risk 激活；
- 路由；
- Approval 请求；
- Handoff；
- Closure 请求。

### System Investigator

负责：

- Observation；
- Hypothesis；
- Evidence Conflict；
- 区分性实验建议。

### RTL Engineer

负责：

- 授权 Scope 内的 fixture RTL 修改；
- 局部自测；
- Implementation Artifact；
- 影响说明。

### Verification Engineer

负责：

- 独立复现；
- 回归；
- Evidence；
- Coverage；
- 验证失败 Blocker。

### Integration Reviewer

负责：

- Evidence 充分性；
- Scope 与 Approval 一致性；
- Claim/Task Result Acceptance；
- 集成风险。

### Engineering Documenter

负责：

- 长期 Record 候选；
- 压缩与去重；
- 引用检查；
- record gate 处置。

## 10.4 Tool 边界

Tool 必须返回结构化结果，不得直接改变：

- Claim Status；
- Gate Status；
- Closure Status；
- Project Status。

安全执行工具必须区分：

```text
tool execution failure
engineering validation failure
```

## 10.5 Approval Adapter

首版至少实现一个可操作入口，例如 CLI：

```text
Approve
Reject
Revoke
Show scope
Show baseline
Show risk
Show retained gates
```

测试中同时提供非交互 Stub。

## 10.6 Gate C：执行边界门禁

必须满足：

- 角色不能绕过 Runtime 直接修改状态；
- Tool 不能直接满足 Gate；
- RTL Engineer 无 WRITE Approval 时不能修改 fixture；
- Verification Engineer 结果可以形成 Evidence，但不能关闭 Task；
- Reviewer 可以接受 Claim/Task Result，但不能伪造 Waiver；
- Documenter 不能创造 Runtime Event；
- 工具失败和验证失败进入不同 Blocker。

---

# 11. Batch 4：QSPI 纵向闭环

## 11.1 目标

使用真实可运行 fixture 完成完整 QSPI 流程。

## 11.2 Fixture 设计

至少准备：

### Baseline A

包含已知拼接缺陷。

必须能够产生：

- 正确 QSPI 输入；
- 错误 FPGA 内部拼接输出；
- 可定位 Observation；
- 可提出但尚未证明的 Hypothesis。

### Baseline B

包含授权后的修复。

必须能够证明：

- 修改范围受控；
- 原 Baseline Evidence 不自动适用于 B；
- 新验证针对 B；
- 通过和失败结果均可以被表达。

## 11.3 两种验证方法

为满足独立性，至少提供两种方法，例如：

```text
RTL self-checking testbench
+ 独立 Python/C++ reference comparison
```

或：

```text
模块级仿真
+ 独立数据序列检查器
```

仅修改测试名称或重复运行同一逻辑，不算独立方法。

## 11.4 必须跑通的成功路径

```text
创建 Task
→ 绑定 Baseline A
→ Investigation
→ 复现异常
→ 激活 Risk
→ WRITE Approval
→ 修改为 Baseline B
→ 旧 Evidence 失效
→ 独立验证 B
→ Reviewer Acceptance
→ Gate 满足
→ record gate 处置
→ CLOSED
```

## 11.5 必须跑通的失败路径

至少包括：

### 验证失败

```text
修改 Artifact
→ 独立验证失败
→ 反证注册
→ Claim CONTRADICTED
→ Gate UNSATISFIED
→ Task REWORK_REQUIRED
```

### Approval 撤销

```text
WRITE 已授予
→ 用户撤销
→ 后续正式写入拒绝
→ 现有 Artifact 待审查
```

### Evidence Conflict

```text
板上 Observation
≠
仿真结果
→ EVIDENCE_CONFLICT Blocker
→ 不允许直接进入修复关闭
```

### Event Store 恢复

```text
执行到中间状态
→ Runtime 重启
→ 从持久化恢复
→ Derived Result 与重启前一致
```

## 11.6 Hardware Gate

若 Milestone 2 不执行真实板级验证：

- `hardware_gate` 应为 `NOT_REQUIRED`，前提是顶层目标明确只声明 fixture/仿真闭环；
- 不得声称真实板上问题已经关闭；
- 不得使用 Waiver 把 fixture 结果包装成板级验证。

## 11.7 Gate D：纵向样板门禁

必须满足：

- 成功路径可重复执行；
- 至少三条失败路径可重复执行；
- Baseline A/B 不混用；
- 两种验证方法结果可追溯；
- Closure 由 Gate 计算；
- 没有角色可以直接设置 `CLOSABLE`；
- 重启恢复后结果一致；
- QSPI 样板不需要新增核心对象或状态。

---

# 12. Batch 5：OMP/pi 原型、记录和冻结

## 12.1 OMP/pi 原型适配

实现最薄适配层：

```text
OMP/pi request
→ Runtime Command
→ Runtime result/events
→ role invocation
→ structured response
```

适配层不得：

- 直接写 Derived Result；
- 绕过 Approval；
- 自建第二套 Task 状态；
- 复制 Runtime 状态到独立记忆；
- 改变枚举和对象语义。

最低适配回归应覆盖开放决策 OI-10 指定的：

```text
S03
S06
S13
S20
S24
```

## 12.2 Runtime Restore

验证：

- 完整事件回放；
- Snapshot + 增量回放；
- command 幂等；
- sequence 冲突；
- Snapshot 与 Event 冲突；
- 不完整引用；
- Schema version 不兼容。

Snapshot 与完整回放的 Derived Result 必须一致。

## 12.3 仓库原生 Record

只实现最小记录闭环：

- Task Record；
- Investigation Record；
- Verification Record 候选；
- record gate 处置结果。

默认不生成：

- 每次命令日志；
- 完整 Event Store 副本；
- 完整聊天记录；
- 大段波形和仿真日志；
- 每个 Package 对应一个 Record。

运行恢复必需状态与长期知识记录必须分离。

## 12.4 更新开放决策

逐项将 OI-01～OI-12 标记为：

```text
CLOSED
PARTIALLY_CLOSED
DEFERRED
REJECTED
```

每项必须引用：

- 实现位置；
- 测试；
- ADR；
- 剩余限制。

## 12.5 Gate E：Milestone 2 冻结门禁

只有满足以下条件才能冻结：

1. 起始和结束 Git Baseline 明确；
2. 24 个契约场景自动化并通过；
3. 8 个组合场景自动化并通过；
4. QSPI 成功路径通过；
5. QSPI 失败和返工路径通过；
6. Event Store 回放确定；
7. Snapshot 与完整回放一致；
8. Command 幂等测试通过；
9. Approval 撤销和失效通过；
10. Baseline 失效传播通过；
11. Scope 越界修改被拒绝；
12. Handoff Acceptance 与技术 Acceptance 分离；
13. Acceptance 与 Waiver 分离；
14. Tool Failure 与 Verification Failure 分离；
15. OMP/pi 指定场景适配通过；
16. Runtime 与 Task Record 不双写；
17. Project Status 无直接写接口；
18. QSPI fixture 不依赖生产私有工程；
19. 无 P0、P1 契约偏差；
20. 未新增通用工作流引擎。

---

# 13. 建议物理结构

具体结构在 Batch 1 冻结，建议从以下最小布局开始：

```text
develoip-copilot/
├─ docs/
│  ├─ execution-contract.md
│  ├─ milestone2-execution-plan.md
│  ├─ milestone2-decisions.md
│  ├─ milestone2-validation-report.md
│  └─ open-implementation-decisions.md
├─ runtime/
│  ├─ core/
│  ├─ policy/
│  ├─ persistence/
│  └─ schema/
├─ roles/
├─ skills/
├─ tools/
├─ adapters/
│  └─ omp-pi/
├─ fixtures/
│  └─ qspi-concat/
└─ tests/
   ├─ contract/
   ├─ integration/
   ├─ restore/
   └─ e2e/
```

该结构是实现建议，不是 Milestone 1.5 契约内容。

如果所选语言生态有更自然的布局，可以调整，但不得形成第二套契约定义。

---

# 14. 测试策略

## 14.1 测试层次

### Schema Tests

验证：

- round-trip；
- 必填字段；
- 枚举；
- 引用；
- schema version；
- 非法对象拒绝。

### Command Tests

验证：

- 前置条件；
- Ownership；
- Approval；
- 幂等；
- 拒绝无部分成功。

### Derived Result Tests

验证：

- Claim；
- Evidence validity；
- Gate；
- Closure；
- Project Status 投影。

### Persistence Tests

验证：

- append-only；
- sequence；
- replay；
- Snapshot；
- 冲突；
- 损坏数据。

### Role Boundary Tests

验证：

- 专业角色只能提出；
- Runtime 才能激活；
- Validator 不能伪造实现；
- Documenter 不能改变状态。

### QSPI E2E Tests

验证：

- 调查；
- Risk；
- Approval；
- 修改；
- 独立验证；
- Reviewer；
- Closure；
- Record。

### OMP/pi Adapter Tests

验证平台调用结果与 Runtime 直接调用一致。

## 14.2 不接受的测试方式

不允许：

- 只检查 Markdown 中是否出现关键词；
- 只检查对象能否创建；
- 通过 Mock 绕开所有 Runtime 规则；
- 在测试中直接设置 Derived Result；
- 把测试实现复制成第二套规则引擎；
- 只测试成功路径；
- 用单一方法冒充独立验证。

---

# 15. 实施纪律

## 15.1 契约驱动

每个实现任务必须注明：

- 对应契约章节；
- 对应场景编号；
- 对应不变量；
- 输入和输出；
- 拒绝条件。

## 15.2 测试优先

每个核心行为遵循：

```text
先添加失败测试
→ 最小实现
→ 测试通过
→ 重构
```

## 15.3 不静默扩大 Scope

如果实现过程中发现需要：

- 新对象；
- 新状态；
- 新角色；
- 新 Gate 语义；
- 新写入口；

必须停止并判断：

1. 是否可以用已有对象表达；
2. 是否只是物理实现问题；
3. 是否属于开放实现决策；
4. 是否构成契约变更。

## 15.4 克制项目记录

Milestone 2 执行过程只在以下事件建议长期记录：

- 实现决策冻结；
- 契约偏差；
- 关键失败根因；
- Milestone Gate 结果；
- 开放决策关闭；
- 最终验证结论。

普通命令和局部调试不写长期 Record。

---

# 16. 主要风险

## 风险一：实现成通用工作流引擎

控制：

- 只实现 QSPI 所需对象和 Risk；
- 不提供 DSL；
- 不提供任意自定义状态；
- 不提供任意 Gate。

## 风险二：代码成为第二套契约

控制：

- 测试引用场景编号；
- Schema 和枚举由单一源生成或校验；
- 实现决策不得重新定义语义；
- 验证报告检查契约偏差。

## 风险三：Agent 只存在于名称中

控制：

- 所有角色必须通过统一 Invocation Interface；
- 必须验证权限和 Handoff；
- 不能用一个自由文本 Agent 模拟全部角色而不保留责任边界。

## 风险四：QSPI fixture 过于虚假

控制：

- 必须具有真实的顺序、边界和拼接问题；
- 必须有 Baseline A/B；
- 必须有独立检查方法；
- 必须有失败和反证路径。

## 风险五：Evidence 看似完整但不可追溯

控制：

- 绑定 Baseline；
- 记录命令、输入和工具；
- Evidence 引用 Artifact；
- 失效传播自动测试。

## 风险六：OMP/pi 适配反向污染 Runtime

控制：

- 使用薄 Adapter；
- Adapter 不保存第二套状态；
- 适配结果与 Runtime 直接调用做一致性测试。

## 风险七：项目记录膨胀

控制：

- Event Store 与长期 Record 分离；
- Package 不自动生成 Record；
- 只保存结论和证据引用；
- 默认不注入全部历史。

## 风险八：过早接入真实硬件

控制：

- Milestone 2 默认禁止设备写操作；
- 外部板级 Evidence 只允许导入；
- 真实设备操作另行授权和评审。

---

# 17. 交付物

Milestone 2 最终应交付：

## 17.1 可运行实现

- Runtime Kernel；
- Event Store；
- Derived Engine；
- Risk Policy；
- Baseline Adapter；
- Approval Adapter；
- Role Invocation Layer；
- OMP/pi Prototype Adapter；
- QSPI Fixture；
- 最小 Skills；
- 最小 Tools。

## 17.2 自动化测试

- 24 个契约场景；
- 8 个跨模型场景；
- QSPI 成功路径；
- QSPI 失败路径；
- Restore；
- Idempotency；
- Scope；
- Adapter consistency。

## 17.3 文档

```text
docs/milestone2-execution-plan.md
docs/milestone2-decisions.md
docs/milestone2-validation-report.md
docs/open-implementation-decisions.md
```

`milestone2-decisions.md` 只记录实现选择，不得成为第二份执行契约。

---

# 18. Milestone 2 状态定义

开始执行：

```text
Milestone 2 — IN PROGRESS
```

完成实现但尚未评审：

```text
Milestone 2 — EXECUTED / PENDING REVIEW
```

满足全部 Gate 并完成冻结评审：

```text
Milestone 2 — EXECUTED / FROZEN
```

若 QSPI 样板迫使修改核心对象、状态或关闭语义：

```text
Milestone 2 — BLOCKED BY CONTRACT DEFECT
```

此时必须返回 Milestone 1.5 处理，不能在实现中绕过。

---

# 19. 推荐执行顺序

```text
1. 冻结 base/develop 起始 commit
2. 完成 Batch 1 技术决策与 Runtime 骨架
3. 将 24 个场景转为自动化测试
4. 完成契约内核
5. 建立角色和 Tool 边界
6. 建立 QSPI fixture
7. 跑通成功与失败闭环
8. 完成 Restore 和 OMP/pi 适配
9. 更新开放决策
10. 生成验证报告
11. 挑战评审
12. 冻结 Milestone 2
```

---

# 20. 最终判定标准

Milestone 2 的核心问题不是：

> 是否已经拥有很多 Agent、Skill 和 Tool。

而是：

> 已冻结的执行契约，是否真的可以控制一次可信的 FPGA Bug 调查、授权修改、独立验证、关闭和恢复。

只有这条纵向链路在成功、失败、撤销、冲突和重启条件下都保持同一语义，Milestone 2 才算完成。
