# Milestone 1.5 Contract Test Scenarios

> 本文件是 `execution-contract.md` 的验证附件，不是第二套规范。所有对象、状态、Command、Event 和规则均以 [execution-contract.md](execution-contract.md) 为准。
> 场景总数：24；跨模型组合场景：C01～C08，共 8 个。

## 使用约定

- `valid baseline` 表示实现、配置、工具和输入均可定位。
- `required Gate` 表示由激活的 Risk Policy 确定的必要 Gate。
- “拒绝”表示不产生成功 Domain Event；系统可产生审计用的拒绝结果，但不能产生部分成功事实。

## S01 — 创建缺少分类的 Task

**Given**

用户提供 QSPI 数据拼接异常目标，但没有 primary domain、Scope 或 Baseline。

**When**

Orchestrator 执行 `CREATE_TASK`。

**Then**

Task 创建成功，Execution Status 为 `PROPOSED`，Closure 为 `OPEN`。

**Reject if**

系统把未分类 Task 直接置为 `READY` 或 `RUNNING`。

**Affected objects**

Task、RuntimeEvent。

**Expected events**

`TASK_CREATED`。

**Expected derived results**

缺少字段清单可查询；不得产生可执行 Approval 或 Gate。

**Related invariants**

I01、I03、I06。

## S02 — 完成分类并绑定 Baseline

**Given**

Task 为 `PROPOSED`，已有 QSPI 调查 Scope、`primary_domain=INTEGRATION`、`task_kind=INVESTIGATE` 和 valid Baseline。

**When**

Orchestrator 执行 `CLASSIFY_TASK`，随后执行 `BIND_BASELINE`。

**Then**

Task 进入 `READY`，执行模式为 `ORCHESTRATED`，Risk/Capability/责任主体可查询。

**Reject if**

没有 Baseline、primary domain 或责任主体仍进入 `READY`。

**Affected objects**

Task、Baseline、RuntimeEvent。

**Expected events**

`TASK_CLASSIFIED`、`BASELINE_BOUND`。

**Expected derived results**

初始 Risk Policy 和必要 Gate 被激活；Closure 为 `OPEN`。

**Related invariants**

I01、I09、I10、I13。

## S03 — 直接写入 Derived Result 必须拒绝

**Given**

Task 有一个 `UNSATISFIED` 的 `protocol_gate`，Claim 仍为 `PROPOSED`。

**When**

任意角色发送 `SET_GATE_STATUS(SATISFIED)` 或 `SET_CLAIM_STATUS(SUPPORTED)`。

**Then**

Command 被拒绝，原 Gate、Claim 和 Closure 不变。

**Reject if**

产生 `GATE_SATISFIED`、`CLAIM_SUPPORTED` 或 `TASK_CLOSABLE` 伪事件。

**Affected objects**

ClosureGate、Claim、Task、RuntimeEvent。

**Expected events**

无成功 Domain Event；返回 `DERIVED_RESULT_WRITE_FORBIDDEN`。

**Expected derived results**

Gate 保持 `UNSATISFIED`，Claim 保持 `PROPOSED`，Closure 保持 `OPEN`。

**Related invariants**

I03、I05、I22。

## S04 — 低风险只读任务可开始

**Given**

一个 `READ`、无写入、无外部设备访问的 `EXPLORE` Task 已为 `READY`，无活动 Blocker。

**When**

Orchestrator 执行 `START_TASK`。

**Then**

Task 进入 `RUNNING`，不要求无关的 WRITE Approval。

**Reject if**

任务 Scope 实际含有 WRITE 或外部设备访问却仍按只读条件开始。

**Affected objects**

Task、Approval、RuntimeEvent。

**Expected events**

`TASK_STARTED`。

**Expected derived results**

Execution Status=`RUNNING`；模式保持既有等级；必要 Gate 不因开始而自动满足。

**Related invariants**

I06、I09、I10。

## S05 — 无权角色不能激活 Task

**Given**

Task 为 `PROPOSED`，专业 Subagent 已提出完整分类，但 Orchestrator 尚未激活。

**When**

专业 Subagent 直接执行 `CLASSIFY_TASK` 以使任务进入 `READY`。

**Then**

Command 被拒绝，Task 保持 `PROPOSED`。

**Reject if**

系统把 `PROPOSE` 当作 `ACTIVATE`，或允许专业角色改变执行模式。

**Affected objects**

Task、RuntimeEvent。

**Expected events**

无成功 Domain Event；返回 `OWNERSHIP_VIOLATION`。

**Expected derived results**

Task 仍不可执行，既有建议保留为待编排输入。

**Related invariants**

I03、I28。

## C01 / S06 — RUNNING 新增 Risk 使原 Approval 失效

**Given**

RTL Task 正在 `RUNNING`，已有只覆盖局部 RTL `WRITE` 的 Approval；调查发现修改会改变 AXIS `tlast` 行为，新增 `PROTOCOL_BEHAVIOR_CHANGE`。

**When**

专业 Subagent 提出 Risk，Orchestrator 执行风险激活和重新评估。

**Then**

协议 Risk 被激活；原 Approval 被标记不足或 `INVALIDATED`；Task 进入 `AWAITING_APPROVAL`；protocol regression Gate 变为必要。

**Reject if**

系统继续沿用原 Approval 修改代码、静默删除新增 Risk，或保持 `RUNNING` 继续正式写入。

**Affected objects**

Task、Risk Factor、Approval、ClosureGate、RuntimeEvent。

**Expected events**

Risk activation fact、`APPROVAL_INVALIDATED`，以及状态变更事实。

**Expected derived results**

执行模式保持或升级但不降级；新增 Validator、E3 和独立方法要求被激活。

**Related invariants**

I09、I10、I11、I28。

## C08 / S07 — WRITE Approval 被撤销

**Given**

RTL Engineer 已获得明确 WRITE Approval，正在授权 Scope 内工作，已注册一个待审查 Artifact。

**When**

User 执行 `REVOKE_APPROVAL`。

**Then**

未完成写任务停止；Task 进入 `AWAITING_APPROVAL` 或 `BLOCKED`；Artifact 标记待审查；未有新授权不得继续注册正式修改。

**Reject if**

撤销后继续写入、把已有 Artifact 自动视为已接受，或删除撤销事实。

**Affected objects**

Approval、Task、Artifact、RuntimeEvent。

**Expected events**

`APPROVAL_REVOKED`，必要时产生状态/Blocker 事实。

**Expected derived results**

相关 Write Gate 不满足；观察性 Evidence 不被自动删除，但正式关闭不可推进。

**Related invariants**

I03、I11、I21、I28。

## S08 — Blocker 恢复必须有条件证据

**Given**

Task 为 `RUNNING`，存在 `TOOL_FAILURE` Blocker，owner 为 Tooling/Environment，resume condition 为“指定版本工具重新完成 E3 构建”。

**When**

工具修复后，验证角色注册满足条件的 Evidence，并执行 `RESOLVE_BLOCKER`。

**Then**

Blocker 进入 resolved，Task 恢复到原可恢复状态或按条件进入 `AWAITING_VALIDATION`。

**Reject if**

没有 owner、resume condition 或支持 Evidence 就直接 `RESOLVE_BLOCKER`。

**Affected objects**

Blocker、Evidence、Task、RuntimeEvent。

**Expected events**

`EVIDENCE_REGISTERED`、`BLOCKER_RESOLVED`。

**Expected derived results**

工具失败不会被改写为设计失败；相关 Gate 仅按新 Evidence 重新计算。

**Related invariants**

I20、I21、I28。

## S09 — Artifact 注册门槛

**Given**

RTL Engineer 生成修改后的 `rtl_patch`，该产物将被 Handoff 和 Verification Evidence 引用，并绑定新 Baseline。

**When**

执行 `REGISTER_ARTIFACT`。

**Then**

Artifact 注册成功，保存 producer、location、Scope、dependencies 和 Baseline。

**Reject if**

location、producer、Baseline 或正式修改范围缺失，或注册一个未被引用的临时缓存作为正式 Artifact。

**Affected objects**

Artifact、Task、Baseline、RuntimeEvent。

**Expected events**

`ARTIFACT_REGISTERED`。

**Expected derived results**

Handoff/Gate 可以引用该 Artifact；尚无 Evidence 或 Acceptance，不得自动改变 Claim/Closure。

**Related invariants**

I03、I13、I25。

## S10 — E3 Evidence 仍需覆盖和独立性

**Given**

Verification Engineer 对明确 Baseline 的 RTL Patch 完成可复现仿真，Evidence 为 E3，使用独立方法但未覆盖错误路径。

**When**

执行 `REGISTER_EVIDENCE` 并关联 implementation Claim。

**Then**

Evidence 可注册并标记 VALID，但相关 Gate 继续 `UNSATISFIED`，因为 coverage 不满足 Risk Policy。

**Reject if**

系统仅凭 E3 把 Claim 置为 `SUPPORTED` 或 Gate 置为 `SATISFIED`。

**Affected objects**

Evidence、Claim、ClosureGate、RuntimeEvent。

**Expected events**

`EVIDENCE_REGISTERED`、`CLAIM_EVIDENCE_LINKED`。

**Expected derived results**

Claim 可能保持 `PROPOSED`；E3、relevance、coverage、independence 分开计算。

**Related invariants**

I13、I14、I21、I22。

## S11 — Claim Type 不允许原地升级

**Given**

System Investigator 创建 `HYPOTHESIS` Claim，随后发现足够的观测支持更强的结论。

**When**

执行 `UPDATE_CLAIM_TYPE(FACT)`，或改为创建新的 `FACT` Claim。

**Then**

前一种 Command 被拒绝；后一种方式创建新 Claim，`derived_from` 指向旧 Claim，旧 Claim 保留。

**Reject if**

修改旧 Claim 的 claim_type、statement 或来源以伪造历史。

**Affected objects**

Claim、Evidence、RuntimeEvent。

**Expected events**

合法路径为 `CLAIM_CREATED`；旧 Claim 不产生覆盖写。

**Expected derived results**

旧 Claim 可为 `SUPERSEDED`，新 Claim 从自己的支持链计算状态。

**Related invariants**

I03、I12、I15。

## C04 / S12 — 验证失败阻止关闭

**Given**

Claim 声称 QSPI 拼接已修复，验证 Evidence 为有效 E3，但新回归结果明确反驳该 Claim。

**When**

Verification Engineer 注册反证并完成 `FINISH_TASK`。

**Then**

反证关联 Claim；Claim 变为 `CONTRADICTED` 或待重新评估；related Gate 为 `UNSATISFIED`；Task 进入 `REWORK_REQUIRED` 或保持开放。

**Reject if**

系统忽略反证、保留 `SUPPORTED`，或允许 `CLOSE_TASK`。

**Affected objects**

Evidence、Claim、Acceptance、ClosureGate、Task。

**Expected events**

`EVIDENCE_REGISTERED`、`CLAIM_EVIDENCE_LINKED`、必要的 `TASK_REWORK_REQUESTED`。

**Expected derived results**

Closure=`OPEN`；Implementation/Simulation/Protocol Gate 至少一个为 `UNSATISFIED`。

**Related invariants**

I15、I21、I22、I28。

## C02 / S13 — Baseline 变化传播到 Gate

**Given**

当前 Claim、Evidence、Acceptance 和 simulation Gate 都绑定 Baseline A；上游 Artifact 被修改并形成 Baseline B。

**When**

Orchestrator 执行 `CHANGE_BASELINE` 并重新绑定 Task。

**Then**

依赖 A 的 Evidence 被 `INVALIDATED` 或 `DEGRADED`；Claim 重新评估；Acceptance 重新评估；Gate 变为 `UNSATISFIED`；Closure 回到 `OPEN`。

**Reject if**

旧 Evidence 继续满足 B 的 Gate，或只更新 Task.baseline_ref 而不传播失效。

**Affected objects**

Baseline、Artifact、Evidence、Claim、Acceptance、ClosureGate、Task。

**Expected events**

`BASELINE_CHANGED`、`EVIDENCE_INVALIDATED`/`EVIDENCE_DEGRADED`。

**Expected derived results**

新 Baseline 需要重新验证和必要的新 Approval；旧历史仍可审计。

**Related invariants**

I11、I13、I16、I22。

## C03 / S14 — Handoff 接受不等于技术接受

**Given**

System Investigator 提交包含 Task、Baseline、Observation Claim 和 Evidence 的 Handoff，下游缺少一个 USEFUL Context 但 MUST_HAVE 完整。

**When**

Verification Engineer 执行 `ACCEPT_HANDOFF`，随后开始复现。

**Then**

Handoff 被接受并允许下游开始；原 Claim 的 Acceptance 仍为 `NOT_REVIEWED`。

**Reject if**

Handoff Acceptance 自动将 Claim 或 Task Result 标记为 `ACCEPTED`。

**Affected objects**

Handoff、Acceptance、Claim、Task。

**Expected events**

`HANDOFF_SUBMITTED`、`HANDOFF_ACCEPTED`。

**Expected derived results**

下游可执行；技术 Gate 仍按 Evidence/Claim/Acceptance 计算。

**Related invariants**

I07、I17、I28。

## S15 — 技术 Acceptance 必须有范围和依据

**Given**

Integration Reviewer 收到实现 Artifact 和验证 Evidence，但 Acceptance 请求没有 Baseline 和 acceptance_scope。

**When**

执行 `RECORD_ACCEPTANCE`。

**Then**

Command 被拒绝，目标保持 `NOT_REVIEWED`。

**Reject if**

只凭“看起来没问题”或 Handoff 已接收就写入 `ACCEPTED`。

**Affected objects**

Acceptance、Artifact、Evidence、Task。

**Expected events**

无成功 `ACCEPTANCE_RECORDED`；返回 `ACCEPTANCE_BASIS_INCOMPLETE`。

**Expected derived results**

相关 Gate 不能使用缺失范围的 Acceptance。

**Related invariants**

I07、I13、I17、I28。

## C05 / S16 — 合法 Waiver 可使 Gate WAIVED

**Given**

hardware validation Gate 存在已知残余风险；Waiver 由 User/Risk Owner 对当前 Baseline 和明确 Scope 签发，含 rationale、conditions 和 validity，无活动冲突 Blocker。

**When**

Orchestrator 执行 `CREATE_WAIVER` 并请求关闭计算。

**Then**

匹配 Gate 变为 `WAIVED`，Waiver 可参与 CLOSABLE 计算。

**Reject if**

Waiver 作用范围、Baseline 或责任主体不匹配，或存在与该风险不相容的活动 Blocker。

**Affected objects**

Waiver、ClosureGate、Task、RuntimeEvent。

**Expected events**

`WAIVER_CREATED`。

**Expected derived results**

Gate=`WAIVED`；Claim 和失败测试的技术状态不改变；Closure 只有在其他 Gate 满足时才可能 `CLOSABLE`。

**Related invariants**

I18、I19、I22。

## S17 — Waiver 越界必须拒绝

**Given**

执行者试图创建 Waiver，将失败的协议回归测试或 Baseline A 的风险覆盖到 Baseline B。

**When**

执行 `CREATE_WAIVER`。

**Then**

Command 被拒绝，Gate 保持 `UNSATISFIED`。

**Reject if**

Waiver 把错误 Claim 变正确、覆盖无效 Baseline、由执行者自行签发或自动传播到后续 Baseline。

**Affected objects**

Waiver、Claim、Evidence、ClosureGate。

**Expected events**

无成功 `WAIVER_CREATED`；返回 `WAIVER_SCOPE_INVALID`。

**Expected derived results**

失败测试仍是失败；Closure 保持 `OPEN`。

**Related invariants**

I18、I19、I28。

## S18 — 关闭计算必须依赖全部必要 Gate

**Given**

Task Result 已被 Integration Reviewer 接受，所有必要 Evidence 和 Claim 针对当前 Baseline 有效，必要 Gate 全为 `SATISFIED` 或合法 `WAIVED`，无活动 Blocker，record_gate 已处置。

**When**

执行 `REQUEST_CLOSURE`，随后由有权主体执行 `CLOSE_TASK`。

**Then**

先得到 Closure=`CLOSABLE`，再产生 `TASK_CLOSED`，Closure=`CLOSED`。

**Reject if**

存在一个必要 Gate=`UNSATISFIED`、活动冲突 Blocker、缺少 Task Result Acceptance 或 record_gate 未处置仍关闭。

**Affected objects**

Task、Acceptance、ClosureGate、Waiver、Blocker、RuntimeEvent。

**Expected events**

`TASK_CLOSURE_REQUESTED`、`TASK_CLOSED`。

**Expected derived results**

所有必要 Gate 的满足/豁免依据可追溯；Project Status 仅投影为 closed。

**Related invariants**

I07、I21、I22、I23、I24。

## S19 — 记录被用户拒绝不阻塞技术关闭

**Given**

技术 Gate 已满足，Documenter 提出长期 Investigation Record，用户明确拒绝写入；运行恢复必需事件已持久化。

**When**

记录流程执行 `ACCEPT_RECORD_DECISION(declined)`，随后请求关闭。

**Then**

`record_gate` 视为 resolved；技术 Closure 可以进入 `CLOSABLE` 并按其他条件关闭。

**Reject if**

用户拒绝长期 Record 导致 Runtime 状态被回滚，或在未处置 record_gate 时直接关闭。

**Affected objects**

Task、Record decision、ClosureGate、RuntimeEvent。

**Expected events**

`RECORD_DECISION_RECORDED`、`TASK_CLOSURE_REQUESTED`。

**Expected derived results**

record_gate 已处置但没有伪造 `RECORD_WRITTEN`；技术 Gate 不受影响。

**Related invariants**

I23、I27。

## S20 — 运行时恢复必须校验事件链

**Given**

会话中断，Task Record 保存了 Task Snapshot、最后 sequence、活动 Approval、Blocker 和当前 Baseline。

**When**

新会话执行 Runtime Restore。

**Then**

系统校验 sequence、引用和 Baseline 后恢复 Runtime，并重新计算 Derived Results；只加载当前任务所需事件。

**Reject if**

快照与事件冲突时静默选择文本较新的状态，或恢复时跳过失效 Approval/活动 Blocker。

**Affected objects**

Task Record、RuntimeEvent、Task、Approval、Blocker、ClosureGate。

**Expected events**

恢复本身不伪造业务 Domain Event；必要时记录恢复检查结果。

**Expected derived results**

状态与事件一致；冲突则 Task=`BLOCKED`，Blocker=`CONTRACT_FAILURE`。

**Related invariants**

I03、I23、I24、I28。

## S21 — 父子 Task 统一状态和 Gate 语义

**Given**

父 Task 分解出一个带 `parent_task_ref` 的子 Task，子 Task 负责协议回归，父 Task 需要其 Gate。

**When**

子 Task 完成但 protocol Gate 未满足，父 Task 请求关闭。

**Then**

父 Task 不能关闭；子 Task 使用同样的三轴、Approval、Baseline、Blocker 和 Acceptance 模型。

**Reject if**

系统以独立 Subtask 状态表绕过子 Task Gate，或父 Task 直接覆盖子 Task 的结果。

**Affected objects**

父 Task、子 Task、ClosureGate、Acceptance。

**Expected events**

子 Task 的正常 Task/Claim/Gate 事件；父 Task 只产生派生重算。

**Expected derived results**

父 Closure=`OPEN`；子 Task 可为 `FINISHED` 但不等于 Accepted/Closed。

**Related invariants**

I02、I06、I07、I22。

## S22 — 同一 Scope 的并发写入必须拒绝

**Given**

RTL Engineer A 已持有 Scope X 的活动写锁/授权并正在运行；RTL Engineer B 试图对同一 Scope X 注册修改。

**When**

B 执行 `REGISTER_ARTIFACT` 或等价正式写操作。

**Then**

Command 被拒绝或创建明确 `SHARED_INFRASTRUCTURE_CHANGE`/冲突 Blocker；A 的工作区修改不被覆盖。

**Reject if**

两个写角色同时修改同一受控范围，或合并冲突被静默处理。

**Affected objects**

Task、Approval、Artifact、Blocker、RuntimeEvent。

**Expected events**

无成功 B 侧正式 Artifact 事实；可产生 `BLOCKER_CREATED`。

**Expected derived results**

只有授权 Scope 的版本可被验证；合并前必须重新检查 Baseline。

**Related invariants**

I25、I26、I28。

## C06 / S23 — 外部硬件 Risk 要求独立来源

**Given**

QSPI 复现需要改变板上硬件状态，Task 新增 `HARDWARE_STATE_CHANGE`，仅有执行者自报日志，没有 User/board validator 的外部来源。

**When**

系统重新计算 Risk Policy 和 hardware Gate。

**Then**

执行模式保持/升级为至少 `ORCHESTRATED`；要求 `EXTERNAL_DEVICE_ACCESS` 和 E2，hardware Gate 保持 `UNSATISFIED`。

**Reject if**

SELF_PRODUCED 日志被当成 `EXTERNAL_SOURCE`，或没有设备授权仍执行板级动作。

**Affected objects**

Task、Risk Factor、Approval、Evidence、ClosureGate。

**Expected events**

Risk activation 和 Approval request；没有合法授权时不产生外部设备执行事实。

**Expected derived results**

Required Independence 包含 `EXTERNAL_SOURCE`；hardware Gate 不满足。

**Related invariants**

I09、I10、I13、I16。

## C07 / S24 — Project Status 不得反向改事实

**Given**

Project Status 投影显示 Task 为 `OPEN`，实际 Task 有一个未解决 `VERIFICATION_FAILURE` Blocker。

**When**

任意角色发送 `SET_PROJECT_STATUS(CLOSED)`，或直接编辑项目摘要后请求关闭。

**Then**

Command 被拒绝；实际 Task、Blocker、Gate 和 Closure 不变。

**Reject if**

项目摘要覆盖 Runtime/Task Record，或以 Project Status 为关闭依据。

**Affected objects**

Project Status、Task、Blocker、ClosureGate、Task Record。

**Expected events**

无成功 Project Status 写事件；返回 `PROJECT_STATUS_READ_ONLY`。

**Expected derived results**

Project Status 继续投影 `OPEN`，来源指向活动 Blocker 和未满足 Gate。

**Related invariants**

I03、I21、I23、I24、I28。
