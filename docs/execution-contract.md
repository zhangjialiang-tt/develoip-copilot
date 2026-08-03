# develoip-copilot Milestone 1.5 Execution Contract

> 版本：v1.0
> 里程碑：Milestone 1.5 — Unified Execution Contract
> 状态：FROZEN
> 适用样板：FPGA QSPI 数据拼接异常的调查、修复、独立验证和记录闭环
> 权威性：本文件是 Milestone 1.5 的唯一权威契约。附件只能引用本文件，不得重新定义对象、状态或事件。

## 1. Scope and Non-goals

### 1.1 Scope

本契约定义一个任务如何被创建、分类、授权、执行、验证、交接、恢复和关闭，以及下列对象之间的可信关系：

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

契约只承诺任务级编排，且只要求能够完整表达 QSPI 纵向样板。平台实现必须支持：

- `DIRECT`、`ROUTED`、`ORCHESTRATED` 三种执行模式；
- `Task` 与可选 `parent_task_ref`，不设置独立 `Subtask` 对象；
- Command 是唯一合法写入口；
- Domain Event 是不可变事实；
- Derived Result 由规则计算，不提供直接写接口；
- Execution、Acceptance、Closure 三轴相互独立；
- Baseline 变化后的证据、Claim、Acceptance 和 Gate 失效传播；
- Runtime 状态持久化和跨会话恢复。

### 1.2 Non-goals

本契约不定义：

- 正式 Subagent 配置、Skill 内容、Tool 实现或 OMP/pi Extension；
- 调度器、通用工作流引擎、通用流程 DSL 或自定义状态机；
- 最终 JSON/YAML Schema、数据库表结构或目录结构；
- 完整 FPGA 风险知识库和实际 QSPI Bug 修复；
- 多级审批、复杂的时间驱动过期模型或任意自定义 Gate；
- 新角色、新平面或对 Milestone 1 架构的重新讨论。

实现期可以选择字段编码、事件存储和平台适配方式，但不得改变本契约语义。

## 2. Terminology and Notation

### 2.1 Normative terms

- **MUST**：实现必须满足，否则 Command 必须拒绝或里程碑不能冻结。
- **MUST NOT**：实现不得提供或执行该行为。
- **SHOULD**：默认采用；偏离时必须留下实现决策记录。
- **MAY**：实现可选，不改变契约结果。

### 2.2 Authority terms

- **Command**：角色请求系统执行的动作，是唯一合法写入口。
- **Domain Event**：Command 通过校验后产生的不可变事实。
- **Derived Result**：由权威对象和规则计算出的结果，不是可写事实。
- **Runtime**：当前会话执行状态的操作权威。
- **Task Record**：跨会话恢复和历史审计的持久化权威。
- **Project Status**：从 Runtime/Task Record 派生的只读投影。
- **Baseline**：定义实现、配置、工具、输入和依赖版本的可识别集合。
- **Scope**：对象允许影响的任务、文件、接口、设备、测试、输入或记录范围。
- **Independent**：不是“不同字符串”或“不同调用者”这一单一布尔判断，而是明确的独立角色、独立方法或外部来源。

### 2.3 Status distinction

```text
FINISHED ≠ ACCEPTED
SUPPORTED ≠ ACCEPTED
ACCEPTED ≠ CLOSED
E3 ≠ sufficient
Handoff ACCEPTED ≠ technical acceptance
Waived ≠ technically correct
```

## 3. Core Object Model

### 3.1 Identity and References

所有持久对象 MUST 具有稳定、唯一、不可复用的 `object_id`，并至少携带：

```text
object_id
object_type
created_at
created_by
source_event_ref
```

对象引用 MUST 使用：

```text
{object_type, object_id}
```

跨对象关系必须保存引用，不得复制一份可独立修改的对象状态。删除不是本契约的状态操作；失效、替代、取消或关闭必须留下可追溯事实。

### 3.2 Task

`Task` 是唯一的可执行工作对象。父任务和子任务都使用同一对象模型：

```text
Task
- task_id
- parent_task_ref: optional Task reference
- goal
- task_kind: EXPLAIN | EXPLORE | INVESTIGATE | DESIGN | IMPLEMENT | VERIFY | REVIEW | DOCUMENT
- primary_domain: RTL | VERIFICATION | FIRMWARE | ALGORITHM | INTEGRATION | TOOLING | DOCUMENTATION
- domains: set of Domain
- risk_factors: set of Risk Factor
- required_capabilities: set of Capability
- execution_mode: DIRECT | ROUTED | ORCHESTRATED
- scope
- task_owner
- baseline_ref
- execution_status
- acceptance_summary: derived
- closure_status: derived
- blocker_refs
- approval_refs
- handoff_refs
- artifact_refs
- evidence_refs
- claim_refs
- gate_refs
- record_gate
```

`parent_task_ref` 只表达层级关系，不引入另一套状态、权限或关闭语义。子任务仍必须独立拥有自己的 `task_id`、Baseline、Blocker、Handoff、Acceptance 和 Closure Gate；父任务的关闭不能绕过未满足的必要子任务 Gate。

### 3.3 Baseline

`Baseline` 是一组可复核的实现条件：

```text
Baseline
- baseline_id
- code_revision_or_workspace_snapshot
- configuration_set
- toolchain_versions
- input_data_refs
- dependency_refs
- captured_at
- captured_by
- validity
```

Baseline 绑定到 Task、Artifact、Evidence、Claim、Acceptance 和适用的 Waiver。无法确认实现版本、关键配置或输入时，不得把对象标记为针对该 Baseline 的有效结果。

### 3.4 Approval

`Approval` 只授权明确 Scope 内的动作，不授权一个没有边界的“继续执行”：

```text
Approval
- approval_id
- subject_ref: Task or operation scope
- requested_capability
- risk_factors
- requested_scope
- baseline_ref
- requested_by
- decision_by
- status: REQUESTED | GRANTED | REJECTED | REVOKED | INVALIDATED
- decision_basis
- invalidation_reason: optional
- created_at
- decided_at: optional
```

`GRANTED` 不是永久事实。撤销、范围扩大、风险增加、Capability 升级、Baseline 改变、目标实质变化或作用对象失效都会使 Approval 进入 `REVOKED` 或 `INVALIDATED`。

### 3.5 Artifact

只有满足以下任一条件的工程产物才必须注册：被 Handoff、Evidence 或 Gate 引用；需要跨会话恢复或长期跟踪；或者修改正式工程资产。

```text
Artifact
- artifact_id
- artifact_type
- location
- producer
- created_at
- baseline_ref
- dependency_refs
- scope
- validity: VALID | DEGRADED | INVALIDATED
- source_event_ref
```

缓存、未被引用的临时中间文件和可重新生成的普通日志通常不注册，但一旦成为 Evidence 或 Gate 的依据，就必须先注册。

### 3.6 Evidence

```text
Evidence
- evidence_id
- evidence_type
- source
- artifact_refs
- execution_ref: optional
- baseline_ref
- producer
- produced_at
- summary
- reproducibility_level: E0 | E1 | E2 | E3
- relevance
- coverage
- independence: set of independence values
- validity: VALID | DEGRADED | INVALIDATED
- source_event_ref
```

Evidence 的独立性只能从以下枚举组合表达：

```text
SELF_PRODUCED
INDEPENDENT_ROLE
INDEPENDENT_METHOD
EXTERNAL_SOURCE
```

含义分别是实现者自有方法、不同责任角色、不同工具/模型/验证方法、用户/板级仪器/外部系统。Risk Policy 明确要求哪一种组合；不允许用 `independent=true` 替代。

### 3.7 Claim

```text
Claim
- claim_id
- statement
- claim_type: FACT | OBSERVATION | INFERENCE | DECISION | HYPOTHESIS
- producer
- scope
- baseline_ref
- supported_by: Evidence references
- contradicted_by: Evidence references
- derived_from: Claim references
- supersedes: Claim reference, optional
- status: PROPOSED | SUPPORTED | CONTRADICTED | SUPERSEDED | INVALIDATED (derived)
- created_at
```

`claim_type` 创建后不可原地修改。语义升级必须创建新 Claim，并通过 `derived_from` 连接旧 Claim；旧 Claim 保留并可被标记为 `SUPERSEDED`、`CONTRADICTED` 或 `INVALIDATED`。

Claim 的 `status` 是 Derived Result：

- 有满足 Risk Policy 的有效支持 Evidence 且无未解决的有效反证时，可为 `SUPPORTED`；
- 有有效反证时至少为 `CONTRADICTED` 或保持待重新评估；
- Baseline 失效或依赖失效时为 `INVALIDATED`；
- 不能通过 Command 直接写入 `SUPPORTED`。

### 3.8 Handoff

```text
Handoff
- handoff_id
- task_ref
- source_role
- target_role
- scope
- authorization_refs
- baseline_ref
- context_package: MUST_HAVE | USEFUL | EXCLUDED entries
- artifact_refs
- evidence_refs
- claim_refs
- blocker_refs
- expected_output
- completion_criteria
- submitted_at
- acceptance_ref: optional
```

`MUST_HAVE`、`USEFUL` 和 `EXCLUDED` 条目都必须注明来源、相关性、新鲜度和失效条件。Handoff 是当前运行时交接 Package，不自动生成长期 Record。

### 3.9 Acceptance

Acceptance 是对技术对象或 Handoff 的有范围接受，不是一个全局布尔值。允许的目标类型只有：

```text
HANDOFF
ARTIFACT
CLAIM
TASK_RESULT
```

每条 Acceptance MUST 包含：

```text
Acceptance
- acceptance_id
- target_type
- target_ref
- accepted_by
- acceptance_scope
- acceptance_basis
- conditions
- baseline_ref
- status: NOT_REVIEWED | ACCEPTED | REJECTED | CONDITIONALLY_ACCEPTED
- accepted_at
```

`RISK` 不是 Acceptance 的合法目标。风险接受必须使用 Waiver。Handoff Acceptance 只决定下游是否可以开始以及是否带条件，不改变 Claim 的技术 Acceptance。

### 3.10 Waiver

```text
Waiver
- waiver_id
- waived_subject
- risk_description
- scope
- baseline_ref
- accepted_by
- rationale
- conditions
- validity
- created_at
```

Waiver 只能由有权承担该风险的主体签发，不能由当前执行者自行签发。Waiver 不得覆盖错误 Claim、失败测试、无效 Baseline 或权限不足，也不自动适用于后续 Baseline。匹配的 Closure Gate 可以成为 `WAIVED`，但必须保留上述全部追溯信息。

### 3.11 Blocker

```text
Blocker
- blocker_id
- blocker_type
- blocker_owner
- description
- required_action
- resume_condition
- affected_refs
- created_at
- resolved_at: optional
```

允许的 `blocker_type`：

```text
INPUT_FAILURE | TOOL_FAILURE | ENVIRONMENT_FAILURE | PERMISSION_FAILURE
IMPLEMENTATION_FAILURE | VERIFICATION_FAILURE | CONTRACT_FAILURE
BASELINE_CONFLICT | EVIDENCE_CONFLICT | EXTERNAL_DEPENDENCY
```

`BLOCKED` 没有默认恢复含义；没有责任主体和可验证 `resume_condition` 的 Blocker 不完整。

### 3.12 ClosureGate

```text
ClosureGate
- gate_id
- gate_type
- target_ref
- required
- status: NOT_REQUIRED | UNSATISFIED | SATISFIED | WAIVED (derived)
- dependency_refs: Claim | Acceptance | Evidence | Waiver | Blocker
- basis
- evidence_refs
- acceptance_refs
- waiver_ref: optional
- conditions
```

典型 Gate：

```text
root_cause_gate
implementation_gate
simulation_gate
hardware_gate
protocol_gate
cdc_gate
integration_gate
risk_acceptance_gate
record_gate
```

Gate 状态由依赖对象和规则计算；不得提供 `SET_GATE_SATISFIED` 或 `SET_CLOSABLE` 写接口。

### 3.13 RuntimeEvent

```text
RuntimeEvent
- event_id
- event_type
- aggregate_type
- aggregate_id
- command_ref
- actor
- sequence
- baseline_ref: optional
- payload
- occurred_at
```

Domain Event 不可修改或删除。相同 `command_id` 的重试必须幂等：最多产生一组领域事实，并返回原结果。

## 4. Ownership and Authority

### 4.1 Roles

契约使用既有架构角色：

- **Top-level Orchestrator**：创建/分类/激活任务，协调权限、风险、交接和派生结果。
- **Professional Subagent**：按专业边界提出和产出工作结果，不得越权关闭高风险问题。
- **Verification Engineer**：设计和执行验证，提供验证 Evidence，不代替 Integration Reviewer 进行整体关闭。
- **Integration Reviewer**：验证跨模块风险、Evidence 充分性并作技术 Acceptance 或返工建议。
- **Engineering Documenter**：校验、压缩和写入长期 Record，不创造 Runtime 状态迁移。
- **User / Risk Owner**：授权、停止、取消或承担明确残余风险；不能改写技术事实。
- **External Validator**：由 Risk Policy 指定的板级、外部系统或独立验证责任方。

### 4.2 Operation matrix

表中未列出的操作必须拒绝。`PROPOSE` 不等于 `ACTIVATE`，`ACCEPT` 不等于 `CLOSE`。

| Object | Professional Subagent | Orchestrator | Integration Reviewer / Validator | Documenter | User / Risk Owner |
| --- | --- | --- | --- | --- | --- |
| Task | PROPOSE, UPDATE(scope-local) | CREATE, UPDATE, ACTIVATE, INVALIDATE | VALIDATE, PROPOSE rework | 无 | CANCEL, STOP, PROPOSE |
| Risk Factor | PROPOSE | ACTIVATE, INVALIDATE only with evidence | VALIDATE | 引用 | STOP, not delete |
| Baseline | PROPOSE, CREATE evidence binding | ACTIVATE, INVALIDATE on change | VALIDATE | 引用 | ACCEPT scope |
| Approval | REQUEST | REQUEST, INVALIDATE on rule change | VALIDATE scope | 无 | GRANT, REJECT, REVOKE |
| Artifact | CREATE | UPDATE registry, ACTIVATE reference | VALIDATE, INVALIDATE on verified change | 引用 | 无 |
| Evidence | CREATE | REGISTER coordination | VALIDATE, INVALIDATE/DEGRADE by rule | 摘要、引用 | CREATE external evidence |
| Claim | CREATE, PROPOSE | 协调 link | VALIDATE, ACCEPT/REJECT target | 校验来源/type | ACCEPT human judgment |
| Handoff | SUBMIT | ACTIVATE/route | ACCEPT/REJECT input usability | 引用 | ACCEPT/REJECT input |
| Acceptance | PROPOSE basis | REGISTER | ACCEPT, REJECT, CONDITIONALLY_ACCEPT | 无 | ACCEPT user scope where authorized |
| Waiver | PROPOSE only | VALIDATE scope | VALIDATE residual risk | 无 | WAIVE |
| Blocker | CREATE, PROPOSE resolution | ACTIVATE owner, resolve coordination | VALIDATE recovery | 引用 | STOP, resolve external decision |
| ClosureGate | 提供依据 | ACTIVATE dependencies, compute | VALIDATE/ACCEPT basis | record_gate handling only | WAIVE risk, CLOSE top task |
| Project Status | 无 | 只读投影刷新 | 只读 | 只读 | 只读 |

### 4.3 Authority rules

1. 只有 Orchestrator 可以使初始分类、风险分类和执行模式在 Runtime 中生效。
2. 专业角色可以提出新增 Risk，但不得静默删除或降低它。
3. User 可以停止或取消 Task，但自然语言不能覆盖风险、证据、权限或 Gate 事实。
4. Integration Reviewer/Validator 的 Acceptance 只能作用于其目标和 Scope。
5. Documenter 只能持久化已发生的事件和经授权的 Record 处置。
6. Project Status 永远是只读投影，不是任何事实的权威来源。

## 5. Commands, Events and Derived Results

### 5.1 Command envelope

每个 Command MUST 包含：

```text
command_id
command_type
actor
target_ref
scope
baseline_ref: when relevant
payload
requested_at
```

系统按以下顺序处理：

```text
Command
→ identity/scope/authority/idempotency validation
→ precondition validation
→ append Domain Event(s)
→ update authoritative object
→ recompute Derived Result
→ persist required runtime state
→ return event refs and derived result
```

失败的 Command 不产生部分成功事实；拒绝结果至少包含 `reject_code`、失败前置条件、受影响对象和恢复建议。

### 5.2 Command catalogue

核心 Command：

```text
CREATE_TASK
CLASSIFY_TASK
BIND_BASELINE
CHANGE_BASELINE
START_TASK
REQUEST_APPROVAL
GRANT_APPROVAL
REJECT_APPROVAL
REVOKE_APPROVAL
INVALIDATE_APPROVAL
REGISTER_ARTIFACT
REGISTER_EVIDENCE
CREATE_CLAIM
LINK_EVIDENCE_TO_CLAIM
SUPERSEDE_CLAIM
SUBMIT_HANDOFF
ACCEPT_HANDOFF
RECORD_ACCEPTANCE
CREATE_WAIVER
CREATE_BLOCKER
RESOLVE_BLOCKER
FINISH_TASK
REQUEST_REWORK
CANCEL_TASK
REQUEST_CLOSURE
CLOSE_TASK
PROPOSE_RECORD
ACCEPT_RECORD_DECISION
WRITE_RECORD
VERIFY_RECORD
```

下列接口名称明确禁止作为写 Command：

```text
SET_EXECUTION_STATUS
SET_CLAIM_STATUS
SET_GATE_STATUS
SET_CLOSURE_STATUS
SET_PROJECT_STATUS
```

查询接口可以返回这些状态，不能接受任意状态值作为写入。

### 5.3 Domain Event catalogue

成功 Command 可产生下列不可变事实：

```text
TASK_CREATED
TASK_CLASSIFIED
BASELINE_BOUND
BASELINE_CHANGED
APPROVAL_REQUESTED
APPROVAL_GRANTED
APPROVAL_REJECTED
APPROVAL_REVOKED
APPROVAL_INVALIDATED
ARTIFACT_REGISTERED
EVIDENCE_REGISTERED
EVIDENCE_DEGRADED
EVIDENCE_INVALIDATED
CLAIM_CREATED
CLAIM_EVIDENCE_LINKED
CLAIM_SUPERSEDED
HANDOFF_SUBMITTED
HANDOFF_ACCEPTED
ACCEPTANCE_RECORDED
WAIVER_CREATED
BLOCKER_CREATED
BLOCKER_RESOLVED
TASK_STARTED
TASK_FINISHED
TASK_REWORK_REQUESTED
TASK_CANCELLED
TASK_CLOSURE_REQUESTED
TASK_CLOSED
RECORD_PROPOSED
RECORD_DECISION_RECORDED
RECORD_WRITTEN
RECORD_VERIFIED
```

`Gate`、`Claim.status`、`Evidence.validity`、`Task.closure_status` 和 `Project Status` 的变化是事件应用后的 Derived Result；除导致其变化的事实事件外，不产生伪造的“直接设置”事件。

## 6. Task Lifecycle and Three-axis State Model

### 6.1 Classification and execution mode

Task 创建后必须显式确定 `task_kind`、`primary_domain`、`risk_factors`、`required_capabilities`、Scope、责任主体和 Baseline。缺任何必需项时保持 `PROPOSED`。

执行模式遵循：

```text
DIRECT → ROUTED → ORCHESTRATED
```

风险、写权限、外部设备访问、跨角色独立验证或多阶段 Handoff 出现时，执行模式只能保持或升级，不得降级。`DIRECT` 不得修改正式设计代码。

QSPI 调查、修复和验证默认使用 `ORCHESTRATED`。

### 6.2 Execution Status

```text
PROPOSED
READY
RUNNING
BLOCKED
AWAITING_APPROVAL
AWAITING_VALIDATION
REWORK_REQUIRED
FINISHED
CANCELLED
```

合法迁移由 Command 触发：

| Current | Command / condition | Next |
| --- | --- | --- |
| none | `CREATE_TASK` | PROPOSED |
| PROPOSED | `CLASSIFY_TASK` 且字段、Scope、Baseline 和责任主体完整 | READY |
| READY | `START_TASK` 且全部当前 Approval 满足 | RUNNING |
| READY/RUNNING | `CREATE_BLOCKER` 且无法推进 | BLOCKED |
| READY/RUNNING | 缺少或失效的必需 Approval | AWAITING_APPROVAL |
| RUNNING | `FINISH_TASK` 且本角色 Completion Criteria 满足 | AWAITING_VALIDATION 或 FINISHED |
| AWAITING_VALIDATION | `RECORD_ACCEPTANCE` 为 REJECTED 或有效验证反证 | REWORK_REQUIRED |
| REWORK_REQUIRED | `START_TASK` 且返工授权、输入和 Baseline 有效 | RUNNING |
| BLOCKED | `RESOLVE_BLOCKER` 且 resume_condition 满足 | 原可恢复状态 |
| AWAITING_APPROVAL | 所需 Approval 全部 GRANTED | READY 或 RUNNING |
| 任意未 CLOSED | `CANCEL_TASK` 且 actor 有权 | CANCELLED |
| FINISHED | `REQUEST_CLOSURE` 但必要 Gate 未满足 | FINISHED，Closure OPEN |
| FINISHED | `REQUEST_CLOSURE` 且必要 Gate 满足 | FINISHED，Closure CLOSABLE |

Closure 轴另行迁移：`OPEN → CLOSABLE` 由 `REQUEST_CLOSURE` 的 Gate 计算产生，`CLOSABLE → CLOSED` 由有权主体执行 `CLOSE_TASK` 产生。Closure 状态不是 Execution Status，不能填入上表的 Task 执行状态字段。
```

一个 Task 同时只能有一个 Execution Status，但可以同时关联多个 Blocker。`AWAITING_APPROVAL` 只用于 Approval 缺失这一直接阻塞原因；其余无法推进情况使用 `BLOCKED`。

### 6.3 Acceptance axis

每个 Acceptance 独立使用：

```text
NOT_REVIEWED | ACCEPTED | REJECTED | CONDITIONALLY_ACCEPTED
```

Task 的 Acceptance summary 是各目标 Acceptance 的派生汇总，不是新的写状态。Handoff Acceptance 与技术 Acceptance 必须使用不同的 `target_type` 和 `acceptance_scope`。

### 6.4 Closure axis

```text
OPEN → CLOSABLE → CLOSED
```

`CLOSABLE` 只由 Closure Gate 计算得到，`CLOSED` 需要显式 `CLOSE_TASK`。任何必要 Gate 变为 `UNSATISFIED`、依赖 Baseline 失效或出现活动 Blocker 时，Closure 必须重新回到 `OPEN`。

## 7. Transition and Rejection Rules

### 7.1 Universal rejection rules

以下任一条件成立，Command MUST 拒绝：

1. `actor` 不在该操作的 Ownership 范围内。
2. Target、Scope、Baseline 或引用对象不存在或不匹配。
3. Command 试图直接写入 Derived Result。
4. 目标当前状态不允许该 Command。
5. Approval 缺失、已拒绝、已撤销、已失效或范围不足。
6. 新增 Risk/Capability 未重新计算模式、Validator、Evidence 和 Gate。
7. Evidence、Claim 或 Acceptance 使用无效 Baseline。
8. Acceptance 的 `target_type=RISK` 或 Waiver 缺少合法风险责任主体。
9. Blocker 没有 owner 或可验证恢复条件。
10. 关闭请求存在未解决反证、必要 Gate 不满足或活动 Blocker。
11. Handoff 把 `EXCLUDED` 内容当成 `MUST_HAVE`，或缺少必要输入来源。
12. 事件 `sequence`、`command_id` 或引用链不一致。

### 7.2 Risk change rule

任何新增 Risk Factor 或 Required Capability 必须产生一次重新评估。重新评估至少计算：

```text
execution_mode
required_permission
required_executor
required_validator
minimum_evidence
required_coverage
required_independence
mandatory_gates
```

若当前 Approval 不能覆盖新结果，必须产生 `APPROVAL_INVALIDATED` 或等价失效事实，Task 进入 `AWAITING_APPROVAL`；系统不得继续正式写入。

### 7.3 Baseline invalidation rule

```text
Baseline changed
→ dependent Artifact validity re-evaluated
→ dependent Evidence INVALIDATED or DEGRADED
→ dependent Claim re-evaluated
→ related Acceptance re-evaluated
→ dependent Gate re-evaluated
→ Closure re-opened when a required Gate is unsatisfied
```

旧 Evidence 和 Claim 保留用于审计，但不得满足新 Baseline 的活动 Gate。

### 7.4 Approval rule

Approval 的 Scope 至少包括目标、动作、修改范围、Capability、Risk Factor 和 Baseline。`WRITE`、`EXTERNAL_DEVICE_ACCESS` 和 `DESTRUCTIVE_OPERATION` 不得只依赖自然语言中的泛化授权。

Approval 撤销后：未完成的对应写任务立即停止；已产生的 Artifact 标记为待审查；未经新授权不得继续注册正式修改或声称完成。已产生的观察性 Evidence 不自动删除。

## 8. Risk Policy Matrix

以下是 Milestone 1.5 的确定性最小矩阵。纵向样板只需激活涉及的行，但实现不得给同一 Risk 使用更弱的默认条件。

| Risk Factor | Required Executor | Required Permission | Required Validator | Minimum Reproducibility | Required Evidence Types | Required Coverage | Required Independence | Mandatory Closure Gates |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXTERNAL_INTERFACE_CHANGE | RTL Engineer | WRITE | Verification Engineer + Integration Reviewer | E3 | interface behavior, compatibility | old/new interface consumers | INDEPENDENT_ROLE + INDEPENDENT_METHOD | interface compatibility, integration |
| PROTOCOL_BEHAVIOR_CHANGE | RTL Engineer | WRITE | Verification Engineer | E3 | protocol regression | handshake, ordering, error/edge paths | INDEPENDENT_METHOD | protocol regression |
| CLOCK_RESET_CHANGE | RTL Engineer | WRITE | Verification Engineer + Integration Reviewer | E3 | timing/reset behavior | affected clocks, reset release and recovery | INDEPENDENT_ROLE + INDEPENDENT_METHOD | clock/reset review |
| CDC_CHANGE | RTL Engineer | WRITE | independent Verification Engineer + Integration Reviewer | E3 | CDC analysis and simulation | all changed crossings | INDEPENDENT_ROLE + INDEPENDENT_METHOD | CDC validation |
| STORAGE_LAYOUT_CHANGE | RTL Engineer | WRITE | Verification Engineer | E3 | layout compatibility | producer/consumer addressing and boundary | INDEPENDENT_METHOD | data layout compatibility |
| NUMERIC_BEHAVIOR_CHANGE | Algorithm or RTL Engineer | WRITE | Algorithm Engineer or Verification Engineer | E2/E3 | model comparison and error analysis | defined numeric domain and edge cases | INDEPENDENT_METHOD | numeric equivalence |
| BUILD_SYSTEM_CHANGE | responsible Engineer | WRITE or STATEFUL_EXECUTE | validator selected by scope | E2/E3 | clean build and dependency result | affected targets | INDEPENDENT_ROLE when release-impacting | clean build |
| HARDWARE_STATE_CHANGE | responsible Engineer | EXTERNAL_DEVICE_ACCESS | User or board validator | E2 | board/instrument observation | declared device state and rollback | EXTERNAL_SOURCE | hardware validation |
| SHARED_INFRASTRUCTURE_CHANGE | responsible Engineer | WRITE | Integration Reviewer | E3 | dependent regression | all declared consumers | INDEPENDENT_ROLE + INDEPENDENT_METHOD | dependent regression |
| BASELINE_CHANGE | Orchestrator | re-bind and re-evaluate | original validator | re-evaluate | new-baseline evidence | affected dependencies | preserve original requirement | evidence validity |

矩阵的 `Required Independence` 是集合约束。Evidence 缺少集合中的任一必要维度时，不能满足该 Risk 的 Gate；E3 仍不自动等于充分。

## 9. Artifact–Evidence–Claim Model

### 9.1 Trust chain

```text
Task
→ Artifact
→ Evidence
→ Claim
→ Acceptance
→ ClosureGate
```

每一跳必须有明确引用、Baseline 和 Scope。Evidence 可以支持或反驳 Claim；Claim 可以被多个 Evidence 支持，也可以同时存在未解决反证。

### 9.2 Validity rules

- Evidence 必须说明 `reproducibility`、`relevance`、`coverage`、`independence`、`validity` 和 Baseline。
- `E0` 只能作为待调查输入，不能单独满足技术 Gate。
- `E1`/`E2` 的使用由 Risk Policy 明确允许；高风险实现和协议变化至少要求 E3。
- 有效反证存在时，Claim 不得派生为无条件 `SUPPORTED`。
- Artifact 被修改、配置/输入/工具变化或 Baseline 不可确认时，依赖 Evidence 至少降级，无法再对应时必须失效。
- 失效传播完成前，不得请求相关 Closure。

### 9.3 Claim evolution

```text
HYPOTHESIS
→ new INFERENCE derived_from HYPOTHESIS
→ new FACT derived_from INFERENCE
```

新 Claim 不得覆盖旧 Claim 的正文或类型。`SUPERSEDED` 只说明语义被新 Claim 取代，不等于旧 Claim 曾经为假；`INVALIDATED` 表示其 Baseline 或依赖不再有效。

## 10. Handoff, Acceptance and Waiver

### 10.1 Handoff acceptance

`ACCEPT_HANDOFF` 只检查输入是否可用、是否允许开始下游任务、是否附带条件。它可以产生：

```text
HANDOFF_ACCEPTED
```

但不得产生 Claim 的 `ACCEPTED`，也不得改变技术 Artifact、Evidence 或 Gate 的状态。下游必须对技术对象另行 `RECORD_ACCEPTANCE`。

### 10.2 Technical acceptance

技术 Acceptance 必须有目标、范围、依据、Baseline、接受主体和条件。`CONDITIONALLY_ACCEPTED` 必须列出可验证条件；条件未满足时，相关 Gate 不能按无条件 Acceptance 计算。

### 10.3 Waiver boundary

合法 Waiver 的条件：

1. `accepted_by` 是被授权的 Risk Owner/User 或明确的责任主体；
2. `scope` 与 Gate/风险完全匹配；
3. Baseline 与 Gate 匹配且仍有效；
4. rationale、conditions、validity 齐全；
5. Waiver 没有掩盖权限不足、失败测试、无效 Evidence 或错误 Claim。

Waiver 只允许匹配 Gate 进入 `WAIVED`。它不改变 Claim 的 `SUPPORTED`/`CONTRADICTED`，也不删除 Blocker；存在与 Waiver 不相容的活动 Blocker 时仍不得关闭。

## 11. Blocker and Failure Recovery

| Failure Type | Default owner | Default recovery | Closure effect |
| --- | --- | --- | --- |
| INPUT_FAILURE | 上游输入提供者 | 补充或更正输入 | 相关任务保持 BLOCKED |
| TOOL_FAILURE | Tooling / Environment | 修复或更换工具 | 不得伪装为设计失败 |
| ENVIRONMENT_FAILURE | 环境维护者 | 恢复可重复环境 | 原结果待重新验证 |
| PERMISSION_FAILURE | Orchestrator / User | 请求或补充授权 | 进入 AWAITING_APPROVAL |
| IMPLEMENTATION_FAILURE | 实现角色 | 返工实现 | implementation Gate UNSATISFIED |
| VERIFICATION_FAILURE | 实现或调查角色 | 返工或重新调查 | 相关 Gate UNSATISFIED |
| CONTRACT_FAILURE | 上游 Artifact 生产者 | 修正 Handoff | 下游不得按完整输入开始 |
| BASELINE_CONFLICT | Orchestrator | 重新绑定 Baseline | 触发失效传播 |
| EVIDENCE_CONFLICT | System Investigator | 设计区分实验 | Claim 保持待评估 |
| EXTERNAL_DEPENDENCY | 外部责任方 | 等待、替代或终止 | 不得由内部自测覆盖 |

`RESOLVE_BLOCKER` 只有在 `resume_condition` 有 Evidence 或明确授权支持时才合法。工具失败、环境失败和验证失败必须保持其真实类型，不能为了让流程继续而改成普通完成。

## 12. Closure Gates

### 12.1 Gate calculation

Gate 由以下依赖计算：

```text
required Gate
+ all required Claim/Evidence/Acceptance valid for current Baseline
+ no unresolved contradicting Evidence
+ all mandatory Validator checks complete
+ no incompatible active Blocker
+ matching Waiver, if status is WAIVED
→ SATISFIED or WAIVED
```

Gate 是 `NOT_REQUIRED`、`UNSATISFIED`、`SATISFIED` 或 `WAIVED` 之一。没有合法依赖时不能通过直接设置把 Gate 变成满足。

### 12.2 Closure calculation

```text
all required Gate ∈ {SATISFIED, WAIVED}
+ no active Blocker incompatible with those Gate
+ current Task Result has required Acceptance
+ record_gate is resolved
→ Closure CLOSABLE
```

`record_gate` 的“resolved”满足以下任一项即可：长期 Record 已写入并验证、用户明确拒绝长期记录、或 Documenter 判定无需记录。长期 Record 的处置不得反向创造技术状态。

顶层 Task 只有在 `CLOSABLE` 且关闭主体有权时才能 `CLOSE_TASK`。关闭后若新 Baseline、反证或失效传播影响必要 Gate，系统必须产生新的开放 Task/变更事实；不得静默篡改已关闭历史。

## 13. Runtime Persistence and Restore

### 13.1 Two persistence classes

运行恢复必需持久化：

- 当前 Task Execution Status、Closure Status 和 Baseline；
- 活动 Blocker 及责任主体；
- 未完成 Approval 及其 Scope；
- 跨会话继续所需的 Handoff、Artifact、Evidence、Claim 和 Gate 引用；
- 事件序列、幂等键和最后一致性检查点。

长期知识建议持久化：

```text
规则判断达到候选门槛
→ Orchestrator 提出记录意图
→ 用户确认或目标授权检查
→ Documenter 校验、压缩、去重
→ 写入长期 Record
→ 写后验证
```

Package 是当前运行时交接产物，Record 是筛选后的长期记录；不是每个 Package 都生成 Record。

### 13.2 Runtime/Record authority

执行期：

```text
Command
→ Runtime Domain Event
→ Runtime Task State
→ persistence candidate
→ Task Record update
→ Project Status refresh
```

跨会话恢复：

```text
Task Record snapshot + required events
→ validate sequence and references
→ restore Runtime Task
→ recompute Derived Results
→ resume only if preconditions still hold
```

恢复不得要求加载全部历史；但任何被当前 Gate、Approval、Blocker 或 Baseline 引用的事件必须可追溯。若快照与事件冲突，恢复进入 `CONTRACT_FAILURE`/`BLOCKED`，不得选择较新的文本值静默覆盖。

### 13.3 Project Status

Project Status 只从权威 Runtime/Task Record 派生，必须反向引用来源。没有 `SET_PROJECT_STATUS` Command；写入摘要不会改变 Task、Claim、Gate 或 Closure。

## 14. Core Invariants

1. 每个 Task 必须显式分类并具有唯一 ID。
2. 父任务和子任务统一使用 Task；不存在独立 Subtask 写模型。
3. Command 是唯一合法写入口。
4. Domain Event 不可变且可追溯到 Command。
5. Derived Result 不提供直接写接口。
6. 一个 Task 同时只有一个 Execution Status。
7. Acceptance 与 Closure 独立建模。
8. `FINISHED` 不等于 `ACCEPTED`，`ACCEPTED` 不等于 `CLOSED`。
9. 风险增加时执行模式只能保持或升级。
10. 新 Risk/Capability 必须重新计算权限、验证、Evidence 和 Gate。
11. 已有 Approval 不自动覆盖新增风险或新 Baseline。
12. Claim Type 创建后不可原地修改。
13. Evidence 必须绑定 Baseline 和明确独立性维度。
14. E3 只表示可复现程度，不表示证据充分。
15. 有效反证不得被静默忽略。
16. Baseline 变化必须触发依赖失效传播。
17. Handoff Acceptance 不改变技术 Acceptance。
18. Risk 使用 Waiver，不使用普通 Acceptance。
19. Waiver 不得把错误、失败或无效 Baseline 伪装成正确。
20. Blocker 必须有责任主体和恢复条件。
21. 验证失败阻止相关 Closure Gate。
22. Closure 只能由 Gate 和合法关闭 Command 决定。
23. Runtime 是执行期状态权威，Task Record 是跨会话持久化权威。
24. Project Status 是只读投影，不是事实权威。
25. 两个写角色不得同时修改同一受控 Scope。
26. 用户未提交修改必须被保护，合并冲突不得静默处理。
27. 记录处置不创造 Runtime 状态迁移。
28. 不满足契约的 Command 必须拒绝并说明恢复条件。

## 15. Contract Test Coverage

完整测试场景位于 [contract-test-scenarios.md](contract-test-scenarios.md)，共 24 个场景，其中 8 个为跨模型组合场景。每个场景至少包含 Given、When、Then、Reject if、Affected objects、Expected events、Expected derived results 和 Related invariants。

QSPI 纵向推演位于 [qspi-contract-walkthrough.md](qspi-contract-walkthrough.md)。实现期开放但不影响本契约冻结的事项位于 [open-implementation-decisions.md](open-implementation-decisions.md)。

## 16. Freeze Decision

Milestone 1.5 达成以下结论：

- Task/Subtask 已统一；
- 对象身份、引用、所有权和唯一写入口已明确；
- Command、Domain Event、Derived Result 已分离；
- Approval 撤销/失效、Risk 升级、Evidence Independence、Baseline 传播、Handoff/Acceptance、Waiver、Failure Recovery、Closure 和 Runtime Restore 均有可拒绝规则；
- QSPI 推演不需要新增对象、角色、平面或通用工作流引擎；
- 附件只提供测试场景、样板推演和实现期决策清单，不与本文件竞争权威性。

因此本契约状态为：

```text
Milestone 1.5 — FROZEN
```
