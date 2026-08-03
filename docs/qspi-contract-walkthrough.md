# QSPI Contract Walkthrough

> 本文件是 [execution-contract.md](execution-contract.md) 的纵向样板推演附件。它只把契约规则应用到一个 QSPI 数据拼接异常，不新增对象、状态、角色或事件语义。

## 1. 样板问题和边界

问题：

> QSPI 总线进入 FPGA 的数据正确，但 FPGA 内部拼接结果疑似错误。

范围：

- 读取 QSPI 输入路径、拼接 RTL、相关时钟/复位、验证环境和必要的板级现象；
- 允许在明确 Approval 和 Baseline 下修改 RTL；
- 由独立 Verification Engineer 验证；
- 由 Integration Reviewer 作跨模块技术 Acceptance；
- 关闭前处理必要 Gate、残余风险和 Runtime/Record。

不在范围内：

- 未经 Risk 重新评估的固件、算法或无关模块修改；
- 直接编辑 Project Status 或 Claim/Gate 状态；
- 以完整聊天记录代替 Handoff；
- 在 Milestone 1.5 阶段决定物理 Schema、目录、Tool 或 Subagent 配置。

## 2. 参与对象

本推演只使用既有契约对象：

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

参与角色为既有角色：Top-level Orchestrator、System Investigator、RTL Engineer、Verification Engineer、Integration Reviewer、Engineering Documenter，以及需要时的 User/board validator。

## 3. 推演主线

### Step 1 — Task 创建与分类

Orchestrator 创建一个 `INVESTIGATE`、primary domain 为 `INTEGRATION` 的 Task，Scope 限定为 QSPI 输入、FPGA 拼接和相关验证路径，初始模式确定为 `ORCHESTRATED`。

必须满足：

- `task_id` 唯一；
- `risk_factors` 至少包含当前已知的 `STORAGE_LAYOUT_CHANGE` 可能性，未知风险不能伪造为已确认；
- `required_capabilities` 初始为 `READ`、`SAFE_EXECUTE`；
- 责任主体、Task Kind、Domain 和 Scope 齐全。

产生：

```text
TASK_CREATED
TASK_CLASSIFIED
```

派生结果：Task 从 `PROPOSED` 到 `READY`，Closure=`OPEN`。

可确定判断：缺少分类、Scope 或责任主体不能 `READY`。

仍依赖自由文本：问题描述、疑似错误边界、初始观察摘要。

### Step 2 — 绑定 Baseline 和最小上下文

Orchestrator 绑定包含代码 revision/workspace snapshot、FPGA 配置、工具版本、QSPI 输入和依赖引用的 Baseline A。System Investigator 只读取 MUST_HAVE Context：输入路径、拼接模块、相关 testbench/日志和版本引用。

产生：

```text
BASELINE_BOUND
```

可确定判断：任何后续 Evidence/Claim 必须引用 Baseline A；无法定位版本时只能产生待调查 Evidence，不能申请关闭。

仍依赖自由文本：某条日志为何与拼接异常相关，以及哪些上下文列为 USEFUL。

### Step 3 — System Investigator 提出 Observation / Hypothesis Claim

System Investigator 注册：

1. `OBSERVATION` Claim：QSPI 输入字节序列与总线观测一致，但 FPGA 内部拼接结果与预期顺序不一致；
2. `HYPOTHESIS` Claim：拼接边界或字节选择逻辑存在错误。

对应 Evidence 记录来源、Artifact、Baseline A、E2/E3 等级、relevance、coverage、validity 和 independence。初始 Hypothesis 只能是 `PROPOSED`，不能直接成为 FACT。

产生：

```text
EVIDENCE_REGISTERED
CLAIM_CREATED
CLAIM_EVIDENCE_LINKED
```

可确定判断：观察与假设类型不能混淆；Claim Type 不可原地升级。

### Step 4 — Verification Engineer 构建复现

通过 Handoff 交给 Verification Engineer：

```text
Task: QSPI Task reference
Scope: QSPI input and FPGA concatenation path
Authorization: READ/SAFE_EXECUTE
Baseline: A
MUST_HAVE: input data, expected order, observed order, relevant RTL/testbench refs
Artifact: investigation package and repro input
Evidence: bus observation and internal observation
Claim: observation/hypothesis refs
Blocker: none
Expected Output: deterministic reproduction
Completion Criteria: E3 reproduction with coverage statement
```

Verification Engineer 执行 `ACCEPT_HANDOFF`。这只代表输入可用并允许开始，不代表接受 Observation/Hypothesis 的技术结论。

产生：

```text
HANDOFF_SUBMITTED
HANDOFF_ACCEPTED
```

Task 保持 `RUNNING`；Claim Acceptance 保持 `NOT_REVIEWED`。

### Step 5 — 处理 Evidence Conflict

若复现结果与初始观察不一致，Verification Engineer 注册新的 Evidence 并关联反证；System Investigator 建立 `EVIDENCE_CONFLICT` Blocker，owner 为调查角色，resume condition 为完成区分性实验。

产生：

```text
EVIDENCE_REGISTERED
CLAIM_EVIDENCE_LINKED
BLOCKER_CREATED
```

派生结果：相关 Claim 不能为无条件 `SUPPORTED`；相关 Gate 为 `UNSATISFIED`；Task 为 `BLOCKED` 或保持 `RUNNING` 但不可进入关闭。

可确定判断：反证不能被覆盖；工具失败和证据冲突保持不同类型。

仍依赖自由文本：区分实验的假设、优先级和解释路径。

### Step 6 — 发现新增 Risk 与 Approval 重评估

区分实验表明修复可能改变 AXIS `tlast` 或 QSPI 拼接协议边界，专业角色提出 `PROTOCOL_BEHAVIOR_CHANGE`。Orchestrator 激活 Risk，重新计算：

```text
execution_mode: ORCHESTRATED
required_permission: WRITE
required_executor: RTL Engineer
required_validator: Verification Engineer
minimum_reproducibility: E3
required_independence: INDEPENDENT_METHOD
mandatory_gate: protocol regression
```

只覆盖 READ/SAFE_EXECUTE 的原 Approval 不足，必须失效或标记不足。Task 进入 `AWAITING_APPROVAL`，直到 User/Risk Owner 对明确 Scope、Baseline A、WRITE Capability 和协议风险作出决定。

产生：

```text
APPROVAL_INVALIDATED
APPROVAL_REQUESTED
```

不能做的事：静默删除 Risk、沿用旧 Approval、把协议风险降级为普通 RTL 修改。

### Step 7 — RTL Engineer 执行授权修改

获得新 WRITE Approval 后，RTL Engineer 只在授权 Scope 内修改拼接逻辑，执行局部自测并说明影响范围。正式修改先以 Artifact 注册，Artifact 绑定 Baseline B（若代码已变更则由 Orchestrator 明确建立 Baseline B），保留对 Baseline A 的关系。

产生：

```text
APPROVAL_GRANTED
BASELINE_CHANGED (若形成 B)
ARTIFACT_REGISTERED
```

若 Baseline 从 A 变为 B，所有依赖 A 的旧 Evidence/Claim/Acceptance/Gate 必须触发失效传播；不能把 A 的验证结果直接套用于 B。

### Step 8 — 建立修复 Handoff

RTL Engineer 向 Verification Engineer 提交第二个 Handoff，至少包含：

- 修改 Artifact、依赖和变更 Scope；
- Baseline B；
- WRITE Approval 引用；
- 原始 Claim、反证和新 Claim 引用；
- 已执行的局部自测及其限制；
- protocol regression 的 Completion Criteria；
- 未解决 Blocker 和待验证条件。

若下游接收，产生 `HANDOFF_ACCEPTED`，但新 Claim 仍未被 Integration Reviewer 技术接受。

### Step 9 — 独立验证

Verification Engineer 采用独立方法执行 E3 回归，覆盖正常、边界、握手、错误和顺序路径，并记录工具、输入、命令、结果和覆盖声明。Evidence 的 independence 至少包含 `INDEPENDENT_ROLE` 或 `INDEPENDENT_METHOD`，具体以 Risk Policy 要求为准。

结果分支：

- 通过：注册 Evidence，Claim 重新计算为 `SUPPORTED`（前提是无有效反证），protocol/simulation Gate 可转为 `SATISFIED`；
- 失败：注册反证，Claim 为 `CONTRADICTED`/待重新评估，相关 Gate `UNSATISFIED`，Task `REWORK_REQUIRED`，不得关闭。

验证结果只说明 Baseline B 在声明条件下的结果，不声称所有硬件环境均已覆盖。

### Step 10 — Integration Reviewer Acceptance

Integration Reviewer 检查：

- Artifact Scope 与 Approval 一致；
- Baseline B 明确；
- Evidence E3、relevance、coverage、independence 足以覆盖新增协议 Risk；
- 旧 Baseline 的 Evidence 没有被误用；
- 反证已解决或有明确残余风险；
- 跨模块和集成 Gate 依据齐全。

Reviewer 对 `TASK_RESULT`、Artifact 或 Claim 单独记录 Acceptance。该 Acceptance 不是 User 的风险 Waiver，也不是 Project Status 写入。

### Step 11 — Closure Gate、Waiver 和关闭

Orchestrator 请求 Closure，系统计算：

```text
root_cause_gate
implementation_gate
simulation_gate
protocol_gate
integration_gate
risk_acceptance_gate (仅在有残余风险时 required)
record_gate
```

每个 Gate 必须为 `SATISFIED` 或有当前 Baseline B、合法主体、匹配 Scope 的 `WAIVED`。如果 hardware validation 并未执行但明确为样板必需，必须保持 `UNSATISFIED`；不能通过普通 Acceptance 代替 Waiver。

所有必要 Gate 满足、Task Result 有 Acceptance、无不相容活动 Blocker、record_gate 已处置后，Closure=`CLOSABLE`。有权主体执行 `CLOSE_TASK`，才产生 `TASK_CLOSED`。

### Step 12 — Runtime 持久化与长期记录

以下状态必须可跨会话恢复：

- Task 的 Execution/Closure 状态和 Baseline B；
- 当前 Approval、Handoff、Artifact、Evidence、Claim、Gate 引用；
- 任何活动 Blocker 和其恢复条件；
- 事件 sequence 和幂等键。

Engineering Documenter 可根据记录门槛提出 Investigation Record。用户拒绝长期知识记录时，记录决策已处置即可，不回滚技术关闭；Documenter 不得创造 `TASK_CLOSED` 或修改 Claim/Gate。

## 4. 契约可确定性结论

### 4.1 可由契约确定

| 判断                       | 契约依据                                                    |
| -------------------------- | ----------------------------------------------------------- |
| Task 是否可开始            | 分类、Scope、Baseline、Approval、Blocker 和状态迁移规则     |
| 新 Risk 是否触发重评估     | Risk change rule 与 Risk Policy Matrix                      |
| 原 Approval 是否可继续使用 | Approval Scope/Baseline/状态校验                            |
| Evidence 是否可用于 Gate   | Baseline、validity、reproducibility、coverage、independence |
| Claim 是否能被支持         | 有效支持 Evidence、无未解决反证、派生规则                   |
| Handoff 是否允许下游开始   | Handoff Acceptance 目标与 MUST_HAVE 检查                    |
| Gate 是否满足/豁免         | Gate dependencies 和 Waiver 边界                            |
| Task 是否可关闭            | 所有必要 Gate、Acceptance、Blocker、record_gate             |
| Runtime 是否可恢复         | Snapshot/event sequence/reference 校验                      |
| Project Status 是否可写    | 不可写，只能由权威状态投影                                  |

### 4.2 仍依赖自由文本或实现选择

- 初始问题陈述和观察摘要的自然语言表达；
- 分区 Scope 的具体文件、接口和输入列表；
- 区分性实验的具体设计与优先级；
- `relevance`、`coverage` 的领域判据在工具层的具体计算方式；
- 事件日志、Snapshot、幂等键和物理 Schema 的存储实现；
- QSPI 板级硬件动作的设备适配与命令包装。

这些内容不能改变状态、权限、Acceptance、Waiver 或关闭语义。

### 4.3 是否被迫新增对象

没有。父子工作使用 `Task.parent_task_ref`；验证包、调查包和长期记录分别是 Artifact/Handoff/Record 的不同用途，不构造新的可写核心对象。Gate 和 Project Status 仍是规则结果/投影，不增加独立状态写模型。

### 4.4 P0 缺口结论

本推演未发现阻止 Milestone 1.5 冻结的 P0 缺口。所有关键路径均有：

- 合法 Command；
- 前置条件和拒绝规则；
- Domain Event 追溯；
- Derived Result 计算；
- 失败责任主体与恢复条件；
- Baseline 失效传播；
- Acceptance/Waiver 边界；
- Runtime 恢复路径。

实现期的具体工具、Schema、存储和平台适配仍列在 [open-implementation-decisions.md](open-implementation-decisions.md)，不得在实现前被误报为已冻结实现。
