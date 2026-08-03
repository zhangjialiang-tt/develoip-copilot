# develoip-copilot Milestone 1.5 执行计划 v1.1

> 里程碑：Unified Execution Contract
> 前置基线：整体架构设计蓝图 v1.2，状态为 `Milestone 1 — FROZEN`
> 计划状态：`EXECUTED`
> 里程碑状态：`Milestone 1.5 — FROZEN`
> 唯一权威交付物：`execution-contract.md`
> 执行方式：5 个 Batch，4 个硬门禁
> 核心目标：形成面向 QSPI 纵向样板的最小、统一、可拒绝、可测试执行契约

---

# 1. 里程碑目标

Milestone 1.5 负责将已冻结架构转换为可执行契约，使系统能够确定性回答：

1. 一个任务如何创建、分类和进入执行；
2. 哪个角色可以提出、创建、激活、验证或关闭对象；
3. 状态只能通过哪些合法操作变化；
4. 风险变化如何影响执行模式、权限、验证和关闭门禁；
5. Artifact、Evidence 和 Claim 如何形成可信链；
6. Handoff 的接收与技术接受如何分离；
7. 风险如何通过 Waiver 处理，而不是伪装成技术接受；
8. 失败后任务返回哪个责任主体；
9. Baseline 变化如何使证据、Claim 和 Gate 失效；
10. Runtime 如何持久化并跨会话恢复；
11. 顶层目标何时能够进入 `CLOSABLE` 和 `CLOSED`；
12. 哪些非法操作必须被拒绝。

本里程碑不设计通用工作流引擎，只服务于：

> FPGA Bug 调查、修复、独立验证和项目记录闭环。

---

# 2. 本里程碑不做什么

不包含：

- 正式 Subagent 配置；
- 正式 Skill 内容；
- OMP/pi Extension；
- 调度器实现；
- 最终 JSON/YAML Schema；
- 数据库设计；
- 通用流程 DSL；
- 自定义状态机；
- 完整 FPGA 风险知识库；
- 实际 QSPI Bug 修复；
- 完整项目生命周期自治；
- 最终目录结构。

不得借契约精化重新讨论：

- 是否增加角色；
- 是否增加第四个横向平面；
- 是否重新合并三轴状态；
- 是否把完整工程职责塞进 Skill；
- 是否改变 Runtime、Task Record、Project Status 的权威关系。

---

# 3. 契约最小核

Milestone 1.5 的 v1 契约只冻结 QSPI 纵向样板实际需要的最小核心。

## 3.1 核心对象

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

## 3.2 不再设置独立 Subtask 对象

所有可执行工作统一使用 `Task`：

```text
Task
- task_id
- parent_task_ref: optional
```

父任务和子任务共用：

- 三轴状态；
- 权限；
- Risk Factor；
- Baseline；
- Blocker；
- Handoff；
- Acceptance；
- Closure Gate。

这样避免形成两套重复对象模型。

## 3.3 核心关系

```text
Task parent_of Task
Task blocked_by Blocker
Task authorized_by Approval
Task bound_to Baseline

Artifact produced_by Task
Artifact depends_on Artifact

Evidence observes Artifact or execution
Evidence supports Claim
Evidence contradicts Claim

Claim applies_to Baseline
Claim derived_from Claim
Claim supersedes Claim

Handoff carries object references
Acceptance targets technical object
Waiver handles accepted residual risk

ClosureGate depends_on Claim, Acceptance, Evidence or Waiver
```

## 3.4 不进入最小核的内容

以下内容留到纵向样板证明有必要后再增加：

- 通用 Dependency Graph 对象；
- 任意自定义 Gate；
- 任意自定义对象类型；
- 多级审批链；
- 时间驱动的复杂 Approval 过期模型；
- 通用规则表达语言；
- 完整事件溯源框架。

---

# 4. 唯一交付入口

唯一权威契约：

```text
execution-contract.md
```

建议章节：

```text
1. Scope and Non-goals
2. Terminology
3. Core Object Model
4. Identity and References
5. Ownership and Authority
6. Commands, Events and Derived Results
7. Three-axis State Model
8. Transition and Rejection Rules
9. Authorization and Approval
10. Risk Policy Matrix
11. Artifact–Evidence–Claim Model
12. Handoff and Acceptance
13. Waiver and Risk Acceptance
14. Blocker and Failure Recovery
15. Closure Gates
16. Runtime Persistence and Restore
17. Core Invariants
18. Contract Test Scenarios
```

评审附件：

```text
contract-test-scenarios.md
qspi-contract-walkthrough.md
open-implementation-decisions.md
```

附件不得重新定义核心对象、状态或事件。

---

# 5. 事件与派生结果模型

## 5.1 三类运行时行为

### Command

外部角色请求系统执行的动作，是唯一合法写入口。

示例：

```text
CREATE_TASK
CLASSIFY_TASK
START_TASK
REQUEST_APPROVAL
GRANT_APPROVAL
INVALIDATE_APPROVAL
REGISTER_ARTIFACT
REGISTER_EVIDENCE
CREATE_CLAIM
SUBMIT_HANDOFF
RECORD_ACCEPTANCE
CREATE_WAIVER
CREATE_BLOCKER
RESOLVE_BLOCKER
CANCEL_TASK
REQUEST_CLOSURE
```

### Domain Event

合法 Command 成功后产生的不可变事实。

示例：

```text
TASK_CREATED
TASK_CLASSIFIED
TASK_STARTED
APPROVAL_GRANTED
APPROVAL_INVALIDATED
ARTIFACT_REGISTERED
EVIDENCE_REGISTERED
CLAIM_CREATED
HANDOFF_SUBMITTED
ACCEPTANCE_RECORDED
WAIVER_CREATED
BLOCKER_CREATED
BLOCKER_RESOLVED
TASK_CANCELLED
GOAL_CLOSED
```

### Derived Result

由当前对象和规则计算出的结果，不提供直接写接口。

示例：

```text
Claim 是否获得支持
Evidence 是否仍有效
Gate 是否满足
Task 是否 CLOSABLE
Project Status 投影
```

## 5.2 核心不变量

```text
Command
→ 校验前置条件
→ 产生 Domain Event
→ 更新权威对象
→ 重新计算 Derived Result
```

禁止：

```text
直接把 Claim 设置为 SUPPORTED
直接把 Gate 设置为 SATISFIED
直接把 Closure 设置为 CLOSABLE
直接修改 Project Status 以改变任务事实
```

人工干预只能通过：

- 新 Evidence；
- Acceptance；
- Waiver；
- Approval；
- 合法状态迁移 Command；

表达。

## 5.3 状态写入规则

所有状态变化必须由合法 Command 和 Domain Event 产生。

平台接口不得同时暴露：

```text
任意状态直接赋值
```

和：

```text
事件驱动状态迁移
```

两条写路径。

---

# 6. Ownership Matrix

每个对象的权限不能只区分“可更新或不可更新”。

必须至少区分：

```text
PROPOSE
CREATE
UPDATE
VALIDATE
ACTIVATE
INVALIDATE
ACCEPT
WAIVE
CLOSE
```

示例语义：

| 对象        | 专业 Subagent | 编排器   | Reviewer        | Documenter     | 用户                |
| ----------- | ------------- | -------- | --------------- | -------------- | ------------------- |
| Risk Factor | PROPOSE       | ACTIVATE | VALIDATE        | 无             | 可停止执行          |
| Artifact    | CREATE        | 注册协调 | VALIDATE        | 引用           | 无                  |
| Evidence    | CREATE        | 注册协调 | VALIDATE        | 持久化摘要     | 可提供外部 Evidence |
| Claim       | CREATE        | 协调     | ACCEPT/REJECT   | 检查类型和来源 | 可接受人工判断      |
| Approval    | REQUEST       | REQUEST  | 无              | 无             | GRANT/REVOKE        |
| Gate        | 无直接写入    | 计算协调 | 提供 Acceptance | 无             | 提供 Waiver         |
| Task State  | 提议迁移      | ACTIVATE | 提议返工        | 不得改变       | 可暂停或取消        |

必须冻结：

- 谁能提出；
- 谁能使其生效；
- 谁能使其失效；
- 谁能接受；
- 谁能关闭。

---

# 7. 三轴状态模型

## 7.1 Execution Status

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

互斥规则：

- `AWAITING_APPROVAL`：唯一直接阻塞原因是所需 Approval 缺失；
- `AWAITING_VALIDATION`：实现执行已完成，下一必要动作是独立验证；
- `BLOCKED`：其他无法推进的情况；
- 一个 Task 同一时刻只有一个 Execution Status；
- 一个 Task 可以同时关联多个 Blocker。

## 7.2 Acceptance Status

```text
NOT_REVIEWED
ACCEPTED
REJECTED
CONDITIONALLY_ACCEPTED
```

Acceptance 只允许挂载：

```text
HANDOFF
ARTIFACT
CLAIM
TASK_RESULT
```

不允许挂载 `RISK`。

每条 Acceptance 必须包含：

```text
target_type
target_ref
accepted_by
acceptance_scope
acceptance_basis
conditions
baseline
accepted_at
```

## 7.3 Closure Status

```text
OPEN
CLOSABLE
CLOSED
```

```text
FINISHED ≠ ACCEPTED
ACCEPTED ≠ CLOSED
SUPPORTED ≠ ACCEPTED
```

Claim 获得支持证据后，Acceptance 仍可以是 `NOT_REVIEWED`。

---

# 8. Waiver 与风险接受

风险接受不使用普通 Acceptance。

## 8.1 Waiver 语义

Waiver 表示：

> 某项风险、缺口或 Gate 条件仍然存在，但合法责任主体明确同意承担该风险并继续。

Waiver 至少包含：

```text
waived_subject
risk_description
scope
baseline
accepted_by
rationale
conditions
validity
created_at
```

## 8.2 Waiver 限制

Waiver 不得：

- 把错误 Claim 变成正确；
- 把失败测试变成通过；
- 覆盖无效 Baseline；
- 覆盖权限不足；
- 由执行者自行签发；
- 自动适用于后续 Baseline。

## 8.3 Gate 与 Waiver

Gate 可以因合法 Waiver 进入：

```text
WAIVED
```

但必须能够追溯：

- 谁接受风险；
- 接受什么；
- 对哪个版本；
- 有何限制；
- 何时失效。

---

# 9. Approval 生命周期

Approval 除批准和拒绝外，必须支持失效。

## 9.1 最小 Command/Event

```text
REQUEST_APPROVAL
GRANT_APPROVAL
REJECT_APPROVAL
INVALIDATE_APPROVAL
```

## 9.2 失效条件

以下情况必须重新评估 Approval：

- 用户主动撤销；
- 修改范围扩大；
- 新增 Risk Factor；
- Required Capability 升级；
- Baseline 改变；
- 任务目标发生实质变化；
- Approval 作用对象失效。

已有 Approval 不得自动覆盖新增风险。

---

# 10. Evidence Independence

Evidence 的独立性不能使用含义模糊的单一布尔值。

最小枚举：

```text
SELF_PRODUCED
INDEPENDENT_ROLE
INDEPENDENT_METHOD
EXTERNAL_SOURCE
```

允许组合。

含义：

- `SELF_PRODUCED`：实现者使用自己的方法产生；
- `INDEPENDENT_ROLE`：由不同责任角色产生；
- `INDEPENDENT_METHOD`：采用不同工具、模型或验证方法；
- `EXTERNAL_SOURCE`：由用户、板级仪器或外部系统提供。

Risk Policy 必须说明需要哪种独立性，而不是笼统写“独立验证”。

---

# 11. 五个执行 Batch

Phase 仍作为 `execution-contract.md` 的章节顺序，但实际执行只使用以下五个 Batch。

---

## Batch 1：控制核心

### 范围

- Scope 与 Non-goals；
- 术语；
- Task 统一模型；
- Identity 与 Reference；
- Ownership Matrix；
- Command / Domain Event / Derived Result；
- Execution Status；
- Blocker。

### 必须解决

1. Subtask 收敛为带 `parent_task_ref` 的 Task；
2. 所有状态变化由合法 Command 产生；
3. 派生状态无直接写入口；
4. Blocker 具有责任主体和恢复条件；
5. Ownership 区分提出与生效。

### 输出位置

全部直接写入：

```text
execution-contract.md
```

不得生成多个准权威对象规范文件。

### Gate A：对象模型门禁

进入 Batch 2 前必须满足：

- Task/Subtask 关系明确；
- 对象身份唯一；
- Ownership Matrix 完成；
- Command、Event、Derived Result 边界明确；
- Acceptance 目标类型预冻结；
- 状态无双写路径。

---

## Batch 2：权限与风险

### 范围

- Capability；
- Approval；
- Approval 失效；
- Risk Factor；
- 执行模式升级；
- Risk Policy Matrix；
- 外部 Validator。

### Risk Policy Matrix 结构

```text
Risk Factor
Required Executor
Required Permission
Required Validator
Minimum Reproducibility
Required Evidence Types
Required Coverage
Required Independence
Mandatory Closure Gates
```

### 关键规则

- 专业 Subagent 可以提出 Risk；
- 编排器负责激活分类；
- Risk 不可被静默删除；
- 用户可以停止任务，但不能把技术风险事实改成“不存在”；
- 新 Risk 必须重新评估模式、权限、证据和 Gate；
- Approval 可以撤销或因范围变化失效。

### Gate B：控制模型门禁

进入 Batch 3 前必须满足：

- Approval 可批准、拒绝、撤销和失效；
- 风险升级路径可测试；
- 执行模式只能保持或升级；
- 样板涉及的 Risk 已具备确定性映射；
- 新增风险不会沿用不充分的旧授权。

---

## Batch 3：可信交付链

### 范围

- Artifact；
- Evidence；
- Evidence Independence；
- Claim；
- Baseline；
- Handoff；
- Acceptance；
- Invalidation。

### Claim 规则

Claim Type：

```text
FACT
OBSERVATION
INFERENCE
DECISION
HYPOTHESIS
```

Claim Type 创建后不允许原地修改。

语义升级通过新 Claim 表达：

```text
HYPOTHESIS
→ DERIVED_FROM
→ INFERENCE
→ DERIVED_FROM
→ FACT
```

旧 Claim 保留并可标记：

```text
SUPERSEDED
CONTRADICTED
INVALIDATED
```

### Evidence 规则

Evidence 至少表达：

```text
reproducibility
relevance
coverage
independence
validity
baseline
```

```text
E3 ≠ sufficient
SUPPORTED ≠ ACCEPTED
```

### Handoff 规则

Handoff 必须包含：

- Task；
- Scope；
- Authorization；
- Baseline；
- MUST_HAVE Context；
- Artifact；
- Evidence；
- Claim；
- Blocker；
- Expected Output；
- Completion Criteria。

Handoff Acceptance 只表示：

- 输入是否可用；
- 是否可以开始下游任务；
- 是否附带条件。

它不自动改变 Claim 的 Acceptance。

### Gate C：可信链门禁

进入 Batch 4 前必须满足：

- Evidence 支持或反驳 Claim 的规则明确；
- Claim 与 Acceptance 完全分离；
- Handoff 接受不改变技术状态；
- Baseline 失效传播闭合；
- Evidence Independence 含义明确；
- 已失效 Evidence 不能满足活动 Gate。

---

## Batch 4：关闭与持久化

### 范围

- Failure Recovery；
- Waiver；
- Closure Gate；
- Persistence；
- Runtime Restore；
- Project Status 投影。

### Persistence Decision 主体

持久化分成两类。

#### 运行恢复必需持久化

例如：

- Task 当前状态；
- 活动 Blocker；
- 当前 Baseline；
- 未完成 Approval；
- 跨会话继续所需的关键引用。

由运行时规则强制产生持久化候选，不依赖用户是否愿意写长期知识记录。

#### 长期知识建议持久化

标准流程：

```text
规则判断达到候选门槛
→ 顶层编排器提出持久化意图
→ 用户确认或目标授权检查
→ Engineering Documenter 校验、压缩、去重
→ 写入长期 Record
→ 写后验证
```

Documenter 不得创造 Runtime 状态迁移。

### Package 与 Record

```text
Package = 当前运行时交接产物
Record = 经过筛选的长期持久化记录
```

不是每个 Package 都生成 Record。

### record_gate

表示记录处置已完成，以下任一情况满足：

- 已写入；
- 用户明确拒绝；
- Documenter 判定无需记录。

### Gate D：冻结前门禁

进入 Batch 5 前必须满足：

- 失败类型有默认恢复路径；
- Waiver 与 Acceptance 已分离；
- Gate 可以由依赖对象计算；
- Project Status 无直接写入口；
- Runtime 与 Task Record 不存在独立双写；
- 跨会话恢复不要求加载全部历史。

---

## Batch 5：契约验证

### 范围

- 单规则测试；
- 跨模型组合测试；
- QSPI Walkthrough；
- 最终冻结评审。

### 测试规模

```text
20～30 个核心场景
```

其中至少：

```text
6 个跨模型组合场景
```

### 必须包含的组合测试

#### 状态与权限组合

```text
RUNNING
+ 新增 Risk
+ 原 Approval 不充分
→ Approval 失效
→ AWAITING_APPROVAL
```

#### Baseline 与证据组合

```text
Baseline changed
→ Evidence invalidated
→ Claim 失去支持
→ Acceptance 重新评估
→ Gate UNSATISFIED
```

#### Handoff 与技术接受组合

```text
Handoff ACCEPTED
→ 下游可以开始
→ Claim Acceptance 仍为 NOT_REVIEWED
```

#### 验证失败与关闭组合

```text
Verification failed
→ Evidence contradicts Claim
→ related Gate UNSATISFIED
→ Closure remains OPEN
```

#### Waiver 与关闭组合

```text
Gate WAIVED
+ Waiver 主体合法
+ Scope 匹配
+ Baseline 匹配
+ 无活动 Blocker
→ 可以参与 CLOSABLE 计算
```

#### Approval 撤销组合

```text
WRITE Approval revoked
→ 未完成写任务停止
→ 已生成 Artifact 标记待审查
→ 不得继续注册正式修改
```

---

# 12. QSPI 桌面推演

样板问题：

> QSPI 总线进入 FPGA 的数据正确，但 FPGA 内部拼接结果疑似错误。

必须验证：

```text
Task 创建与分类
→ ORCHESTRATED 模式
→ Baseline 绑定
→ System Investigator
→ Observation / Hypothesis Claim
→ Verification Engineer 构建复现
→ Evidence Conflict
→ 新增 Risk
→ Approval 重评估
→ RTL Engineer 修改
→ Artifact 注册
→ Verification Engineer 独立验证
→ Claim 支持或反驳
→ Integration Reviewer Acceptance
→ Closure Gate
→ Waiver（如有）
→ Runtime 持久化
→ Investigation Record
```

推演输出必须指出：

- 哪些判断可由契约确定；
- 哪些仍依赖自由文本；
- 哪些是实现期开放项；
- 是否被迫新增对象；
- 是否存在绕过 Approval、Evidence 或 Gate 的路径。

QSPI 推演出现 P0 缺口时，不得冻结 Milestone 1.5。

---

# 13. 契约测试格式

每个测试至少包含：

```text
Given
When
Then
Reject if
Affected objects
Expected events
Expected derived results
Related invariants
```

示例：

```text
Given:
Task 正在 RUNNING，已有局部 RTL WRITE Approval。

When:
RTL Engineer 发现修改会改变 AXIS tlast 行为并提出
PROTOCOL_BEHAVIOR_CHANGE。

Then:
风险被编排器激活；
原 Approval 被标记不足或失效；
执行模式保持 ORCHESTRATED；
Task 进入 AWAITING_APPROVAL；
protocol regression gate 被设为 required。

Reject if:
系统继续沿用原 Approval 修改代码；
系统静默删除新增 Risk；
系统保持 READY 或 RUNNING 并继续执行。
```

---

# 14. 主要风险与控制措施

## 风险一：契约膨胀成通用工作流引擎

控制：

- 只实现契约最小核；
- 只覆盖 QSPI 样板需要；
- 不提供自定义状态、对象和 DSL；
- 新对象必须证明具有独立生命周期。

## 风险二：事件与状态双重写入

控制：

- Command 是唯一写入口；
- Domain Event 不可变；
- Derived Result 只能计算；
- 不提供任意状态赋值接口。

## 风险三：派生结果被当成权威对象修改

控制：

以下内容禁止直接设置：

- Claim 是否获得支持；
- Gate 是否满足；
- Closure 是否 CLOSABLE；
- Project Status。

## 风险四：Acceptance 退化为通用决策对象

控制：

- Acceptance 只处理技术对象；
- Risk 使用 Waiver；
- Handoff 接收与技术接受分离。

## 风险五：对象和事件数量失控

控制：

- Task/Subtask 合并；
- 派生结果不定义独立写事件；
- 可计算的信息不增加可写对象；
- 每个对象必须有独立生命周期或责任主体。

## 风险六：单规则测试产生虚假完备性

控制：

- 至少 6 个组合测试；
- 每个 Gate 至少有失败路径；
- 至少一次验证 Baseline 失效传播；
- 至少一次验证 Approval 撤销；
- 至少一次验证 Waiver 越界被拒绝。

## 风险七：长期记录反向阻塞工程

控制：

- record gate 只要求处置；
- 运行恢复状态与长期知识记录分离；
- 用户拒绝长期记录不影响技术关闭；
- Documenter 不修改 Runtime 状态。

---

# 15. 最终交付物

## 权威契约

```text
execution-contract.md
```

## 验证附件

```text
contract-test-scenarios.md
qspi-contract-walkthrough.md
open-implementation-decisions.md
```

## 不允许出现

- 独立的第二套术语表；
- 独立的状态机权威文档；
- 附件重新定义对象；
- 样板文档引入未进入契约的新规则；
- 多份互相竞争的 Risk Matrix。

---

# 16. Milestone 1.5 完成门槛

只有同时满足以下条件，才能标记：

```text
Milestone 1.5 — FROZEN
```

1. Task/Subtask 已统一；
2. 所有对象身份和所有权明确；
3. Command、Domain Event、Derived Result 完全分离；
4. 状态不存在直接写入和事件写入双路径；
5. Approval 支持撤销和失效；
6. Risk 能确定性驱动权限、验证、Evidence 和 Gate；
7. Acceptance 与 Waiver 分离；
8. Artifact–Evidence–Claim–Acceptance 链闭合；
9. Evidence Independence 定义明确；
10. Baseline 失效传播闭合；
11. Handoff Acceptance 不改变技术接受状态；
12. Failure Recovery 具有默认责任主体；
13. Closure Gate 可以计算；
14. Runtime 与 Task Record 不双写；
15. Project Status 是只读投影；
16. 单规则测试覆盖核心不变量；
17. 至少 6 个跨模型组合测试通过；
18. QSPI 桌面推演无 P0 缺口；
19. 附件没有重新定义契约；
20. 无需新增角色、平面或通用工作流引擎。

---

# 17. 后续里程碑入口

Milestone 1.5 冻结后进入：

```text
Milestone 2 — QSPI Vertical Slice Design
```

Milestone 2 才开始确定：

- 最小运行时实现；
- 首批 Subagent 配置；
- 首批 Skill；
- 首批 Tool；
- 最小物理 Schema；
- 仓库记录目录；
- OMP/pi 原型适配；
- Git worktree 或工作区策略。

在 Milestone 1.5 冻结前，不启动正式实现。
