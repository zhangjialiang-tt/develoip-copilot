# develoip-copilot 整体架构设计蓝图 v1.2

> 暂定名称：`develoip-copilot`
> 文档性质：全局架构与运行时契约蓝图
> 冻结状态：Milestone 1 候选冻结版
> 当前阶段：不生成正式 Skill、Subagent、Schema、脚本或平台配置
> 目标平台：平台中立设计，后续重点适配 OMP/pi

---

# 1. 项目定位

`develoip-copilot` 是一套面向 FPGA、嵌入式固件和基础图像算法开发的工程 Agent 能力体系。

它覆盖：

- Verilog、SystemVerilog、VHDL 等 RTL 开发；
- FPGA 仿真、回归、时序分析与板级问题定位；
- RISC-V 软核上的 C 固件和外设驱动；
- Python、MATLAB、C++ 图像与信号处理参考模型；
- RTL、固件、算法模型之间的一致性验证；
- 设计方案、调试报告、验证记录和项目发展记录维护。

系统的目标不是让 Agent 无限制替代工程师，而是：

> 在权限受控、任务状态明确、证据可追溯、实现与验证适度隔离的前提下，让 Agent 承担工程中的重复劳动和执行性工作。

---

# 2. 第一阶段目标

第一阶段完成：

1. 冻结能力体系的全局架构；
2. 冻结最小运行时契约；
3. 选择一个真实 FPGA Bug 作为纵向样板验证架构。

第一阶段不完成：

- 全量 Skill；
- 全量 Subagent；
- 完整 OMP/pi Extension；
- 无人值守开发；
- 完整项目生命周期自治；
- 全 FPGA 场景风险规则；
- 目录和字段的最终物理格式。

成功标准：

> 后续增加 Agent、Skill、Tool 和平台适配时，不需要重新划分核心职责，也不需要重做任务、权限、证据、接受和关闭模型。

---

# 3. 总体架构

```text
用户
  │
  ▼
顶层编排 Agent
  │
  ▼
任务运行时
  │
  ▼
专业 Subagent
  │
  ▼
Skills + Tools
```

三个横向平面：

```text
Control Plane
- 任务分类
- 执行模式
- 状态管理
- 权限审批
- 路由依赖
- 风险策略
- 失败恢复
- 接受与关闭

Evidence Plane
- Artifact Registry
- Evidence Registry
- Claim Registry
- Baseline Binding
- Evidence Invalidation
- Acceptance Basis

Knowledge Plane
- Task Record
- Investigation Record
- Decision Record
- Verification Record
- Knowledge Record
- Project Status
- Change/Event Log
```

---

# 4. 核心分工

## 4.1 顶层编排 Agent

负责：

- 理解用户目标；
- 选择执行模式；
- 分类任务；
- 判断风险；
- 确定权限；
- 拆分任务；
- 选择 Subagent；
- 建立依赖；
- 管理审批；
- 绑定基线；
- 处理失败和冲突；
- 执行关闭门禁；
- 决定是否建议写入项目记录。

不负责：

- 承担复杂专业实现；
- 替代验证者；
- 直接维护长期项目事实；
- 微观调度每条命令；
- 自行扩大授权范围。

## 4.2 Subagent

Subagent 对完整专业结果负责。

领域角色：

- RTL Engineer
- Verification Engineer
- Firmware Engineer
- Algorithm Engineer

跨领域角色：

- System Investigator
- Engineering Documenter
- Integration Reviewer

## 4.3 Skill

Skill 只承载稳定、复用、平台中立的方法和规范。

Skill 不负责：

- 完整工程目标；
- 长期状态；
- 权限隔离；
- 多 Agent 调度；
- 顶层关闭判断。

## 4.4 Tool

Tool 负责确定性操作：

- 扫描；
- 解析；
- 编译；
- 仿真；
- 比较；
- 数据提取；
- Git 状态采集；
- 引用和一致性校验。

---

# 5. 执行模式

系统支持三种执行模式。

## 5.1 DIRECT

用于：

- 解释；
- 少量文件读取；
- 低风险信息提取；
- 已有安全工具执行；
- 临时说明生成。

DIRECT 模式不得：

- 修改正式 RTL；
- 修改正式固件；
- 修改生产算法；
- 改变外部接口；
- 关闭高风险任务。

## 5.2 ROUTED

由一个主要专业 Subagent 完成边界明确的任务。

例如：

- 分析时序报告；
- 编写外设驱动；
- 生成 testbench；
- 建立参考模型。

## 5.3 ORCHESTRATED

用于：

- 多角色协作；
- 多步骤任务；
- 权限升级；
- 实现与验证隔离；
- 调查、修复、回归和关闭闭环。

## 5.4 执行模式升级原则

执行模式只能保持或升级。

```text
DIRECT → ROUTED → ORCHESTRATED
```

当出现新增风险因素、写权限需求或独立验证要求时，必须升级。

不得因减少流程成本而静默降级。

---

# 6. 任务分类模型

每个任务必须具有显式分类。

## 6.1 Task Kind

```text
EXPLAIN
EXPLORE
INVESTIGATE
DESIGN
IMPLEMENT
VERIFY
REVIEW
DOCUMENT
```

## 6.2 Domain

```text
RTL
VERIFICATION
FIRMWARE
ALGORITHM
INTEGRATION
TOOLING
DOCUMENTATION
```

任务可以包含多个领域，但必须有一个主要责任域。

## 6.3 Risk Factor

```text
EXTERNAL_INTERFACE_CHANGE
PROTOCOL_BEHAVIOR_CHANGE
CLOCK_RESET_CHANGE
CDC_CHANGE
STORAGE_LAYOUT_CHANGE
NUMERIC_BEHAVIOR_CHANGE
BUILD_SYSTEM_CHANGE
HARDWARE_STATE_CHANGE
SHARED_INFRASTRUCTURE_CHANGE
BASELINE_CHANGE
```

## 6.4 Required Capability

```text
READ
SAFE_EXECUTE
STATEFUL_EXECUTE
WRITE
EXTERNAL_DEVICE_ACCESS
DESTRUCTIVE_OPERATION
```

## 6.5 分类责任

- 顶层编排器创建初始分类；
- 专业 Subagent 可以发现并提出新增风险；
- 专业 Subagent不得静默删除风险；
- 用户可以否决执行，但不能通过自然语言覆盖技术风险事实；
- 风险变化必须触发重新评估。

## 6.6 风险变化不变量

任何新增风险因素或能力需求都必须重新评估：

- 执行模式；
- 权限；
- 验证角色；
- 最低证据要求；
- 关闭门禁。

已有授权不得自动覆盖新增风险。

---

# 7. 任务运行时对象

任务运行时管理当前执行目标，不等同于长期项目记录。

最小对象：

```text
Task
Subtask
Artifact
Evidence
Claim
Approval
Handoff
Blocker
Acceptance
ClosureGate
Baseline
```

---

# 8. 三轴状态模型

v1.2 不再把执行完成、接受和关闭混在一个线性状态机中。

## 8.1 Execution Status

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

### PROPOSED

任务已识别，但范围、输入或分类未充分确定。

### READY

执行条件满足。

### RUNNING

专业角色正在执行。

### BLOCKED

存在阻塞，无法正常继续。

### AWAITING_APPROVAL

需要额外权限或用户决策。

### AWAITING_VALIDATION

实现产物已完成，等待独立验证或审查。

### REWORK_REQUIRED

产物未被接受，需返回上游。

### FINISHED

当前执行角色完成约定产物。

### CANCELLED

任务终止。

## 8.2 Acceptance Status

```text
NOT_REVIEWED
ACCEPTED
REJECTED
CONDITIONALLY_ACCEPTED
```

Acceptance 不是单一全局布尔值。

每次接受必须记录：

- `accepted_by`
- `acceptance_scope`
- `acceptance_basis`
- `accepted_at`
- `conditions`
- `baseline`

可能存在：

```text
handoff acceptance
technical acceptance
verification acceptance
risk acceptance
user acceptance
```

## 8.3 Closure Status

```text
OPEN
CLOSABLE
CLOSED
```

### OPEN

至少一个必要关闭门禁未满足。

### CLOSABLE

必要门禁已满足，等待最终关闭动作或用户风险接受。

### CLOSED

顶层目标正式关闭。

## 8.4 核心语义

```text
FINISHED ≠ ACCEPTED
ACCEPTED ≠ CLOSED
```

一个 Subagent 完成任务，不等于下游接受。

一个技术产物被接受，不等于顶层目标关闭。

---

# 9. Blocker 模型

`BLOCKED` 只是执行状态，具体恢复逻辑由 Blocker 描述。

每个 Blocker 至少包含：

```text
blocker_type
blocker_owner
description
required_action
resume_condition
created_at
```

Blocker 类型：

```text
INPUT_FAILURE
TOOL_FAILURE
ENVIRONMENT_FAILURE
PERMISSION_FAILURE
IMPLEMENTATION_FAILURE
VERIFICATION_FAILURE
CONTRACT_FAILURE
BASELINE_CONFLICT
EVIDENCE_CONFLICT
EXTERNAL_DEPENDENCY
```

---

# 10. Runtime 与长期记录权威关系

## 10.1 执行期间

Runtime Task State 是当前执行状态的操作权威。

所有状态变化先发生在运行时。

## 10.2 持久化

达到持久化条件时：

```text
Runtime transition
→ Persistence Event
→ Task Record update
→ Project Status refresh
```

## 10.3 跨会话恢复

```text
Task Record
→ Restore Runtime Task
```

Task Record 是跨会话恢复和历史审计权威。

## 10.4 Project Status

Project Status 仅为当前状态投影：

- 不参与状态变更；
- 不反向修改 Task Record；
- 不反向修改 Runtime；
- 只能由权威记录派生。

## 10.5 禁止双写

Runtime 和 Task Record 不得被两个角色独立修改为不同状态。

Engineering Documenter 只能持久化已发生的运行时事件，不能自行创造状态迁移。

---

# 11. Subagent 角色边界

## 11.1 System Investigator

目标：

> 缩小未知问题的不确定性。

负责：

- 问题陈述；
- 事实和观察；
- 证据索引；
- 假设；
- 区分性实验；
- 排除方向；
- 根因状态；
- 下一步建议。

默认不修改正式代码。

## 11.2 RTL Engineer

目标：

> 交付授权范围内的 RTL 实现结果。

负责：

- RTL 设计；
- RTL 修改；
- 局部自测；
- 修改说明；
- 影响分析。

不得声明高风险问题最终关闭。

## 11.3 Verification Engineer

目标：

> 说明明确版本在明确测试条件下的验证结果。

负责：

- 验证目标；
- 验证环境；
- testbench；
- 激励和检查器；
- 回归；
- 失败分析；
- 覆盖缺口。

不决定整体证据是否足以关闭问题。

## 11.4 Integration Reviewer

目标：

> 判断现有实现和证据是否足以接受和关闭。

负责：

- 跨模块影响；
- 风险覆盖；
- 证据充分性；
- 验证覆盖；
- 遗留风险；
- 接受、返工或阻塞建议。

## 11.5 Firmware Engineer

负责：

- RISC-V/C 固件；
- 外设驱动；
- FPGA 寄存器访问；
- 协议控制；
- 固件构建与测试。

## 11.6 Algorithm Engineer

负责：

- Python、MATLAB、C++ 模型；
- 算法验证；
- 定点化；
- 误差分析；
- 模型与 RTL 一致性。

## 11.7 Engineering Documenter

负责：

- 压缩工作结果；
- 维护仓库原生记录；
- 检查事实类型；
- 检查来源；
- 去重；
- 更新状态投影。

可以拒绝：

- 无来源事实；
- 将推断写成事实；
- 与权威记录冲突；
- 低价值流水账；
- 不满足持久化条件的临时状态。

---

# 12. Artifact 模型

Artifact 是任务产生或修改的重要工程产物。

## 12.1 应注册的 Artifact

满足任一条件应注册：

- 被 Handoff 引用；
- 被 Evidence 引用；
- 被 Closure Gate 依赖；
- 需要跨会话恢复；
- 需要长期跟踪有效性；
- 修改了正式工程资产。

## 12.2 不必注册的内容

通常不注册：

- 可重新生成的缓存；
- 未被引用的中间文件；
- 工具内部临时文件；
- 无长期价值的普通日志；
- 无关构建产物。

## 12.3 Artifact 最小语义

```text
artifact_type
location
producer
created_at
baseline
dependencies
scope
validity
```

---

# 13. Evidence 模型

Evidence 是支持或反驳某项 Claim 的信息。

## 13.1 Evidence 基本语义

```text
evidence_type
source
artifact_ref
baseline
producer
produced_at
summary
reproducibility_level
relevance
coverage
validity
```

## 13.2 Reproducibility Level

### E0：声明

仅有 Agent 或人员陈述。

### E1：观察

有人工或工具观察，但复现信息有限。

### E2：可定位

有明确日志、波形、数据或结果引用，并绑定版本。

### E3：可复现

有明确命令、环境、输入、版本和结果，可重复执行。

## 13.3 重要限制

E3 只代表可复现程度高，不自动代表：

- 覆盖充分；
- 结论正确；
- 系统级关闭充分。

证据充分性由：

- relevance；
- coverage；
- 独立性；
- 风险策略；
- Integration Reviewer；

共同判断。

---

# 14. Claim 模型

Claim 是工程主体对某件事提出的显式主张。

没有 Claim，Evidence 无法明确说明“支持什么”。

## 14.1 Claim 最小语义

```text
statement
claim_type
producer
scope
baseline
supported_by
contradicted_by
confidence
status
```

## 14.2 Claim Type

```text
FACT
OBSERVATION
INFERENCE
DECISION
HYPOTHESIS
```

## 14.3 Claim Status

```text
PROPOSED
SUPPORTED
CONTRADICTED
SUPERSEDED
INVALIDATED
```

## 14.4 核心链路

```text
Artifact
→ Evidence
→ Claim
→ Acceptance
→ Closure Gate
```

## 14.5 反证要求

任何 Claim 都可以同时关联：

- 支持证据；
- 反证；
- 未解决冲突。

存在有效反证时，不得静默将 Claim 视为已确认。

---

# 15. Baseline 与失效传播

验证和 Claim 必须绑定明确 Baseline。

Baseline 可以是：

- commit；
- 工作区快照；
- Artifact 版本；
- 配置集合；
- 工具版本；
- 关键输入数据。

必须能够回答：

> 这项 Claim 和 Evidence 对应的是哪个实现版本、哪些配置和哪些输入。

以下变化可能触发失效：

- 上游 Artifact 改变；
- 配置改变；
- 测试输入改变；
- 工具链相关改变；
- 依赖基线改变；
- 版本无法确认。

失效传播：

```text
Artifact changed
→ dependent Evidence invalidated or degraded
→ dependent Claim re-evaluated
→ Acceptance re-evaluated
→ Closure Gate re-evaluated
```

不得静默保留旧结论。

---

# 16. 权限模型

权限级别：

```text
READ
SAFE_EXECUTE
STATEFUL_EXECUTE
WRITE
EXTERNAL_DEVICE_ACCESS
DESTRUCTIVE_OPERATION
```

## 16.1 默认风险分级审批

- READ：通常自动允许；
- SAFE_EXECUTE：明确安全时自动允许；
- STATEFUL_EXECUTE：需声明影响范围；
- WRITE：修改正式工程资产前必须授权；
- EXTERNAL_DEVICE_ACCESS：单独授权；
- DESTRUCTIVE_OPERATION：逐次确认。

## 16.2 目标授权

目标授权必须明确：

- 目标；
- 读取范围；
- 修改范围；
- 执行权限；
- 设备权限；
- 自动记录权限；
- 保留的强制门禁。

目标授权不覆盖后续新增风险。

---

# 17. 风险策略矩阵

架构冻结矩阵结构，不要求第一阶段覆盖全部场景。

每项风险必须映射到：

```text
Risk Factor
→ Required Permission
→ Required Executor
→ Required Validator
→ Minimum Evidence
→ Closure Gate
```

初始核心矩阵：

| Risk Factor                  | Permission               | Validator                                    | Minimum evidence | Mandatory gate            |
| ---------------------------- | ------------------------ | -------------------------------------------- | ---------------- | ------------------------- |
| EXTERNAL_INTERFACE_CHANGE    | WRITE                    | Verification Engineer + Integration Reviewer | E3 且覆盖兼容性  | interface compatibility   |
| PROTOCOL_BEHAVIOR_CHANGE     | WRITE                    | Verification Engineer                        | E3               | protocol regression       |
| CLOCK_RESET_CHANGE           | WRITE                    | Verification Engineer + Integration Reviewer | E3               | clock/reset review        |
| CDC_CHANGE                   | WRITE                    | 独立验证与集成审查                           | E3               | CDC validation            |
| STORAGE_LAYOUT_CHANGE        | WRITE                    | Verification Engineer                        | E3               | data layout compatibility |
| NUMERIC_BEHAVIOR_CHANGE      | WRITE                    | Algorithm Engineer 或 Verification Engineer  | E2/E3            | numeric equivalence       |
| BUILD_SYSTEM_CHANGE          | WRITE / STATEFUL_EXECUTE | 视范围决定                                   | E2/E3            | clean build               |
| HARDWARE_STATE_CHANGE        | EXTERNAL_DEVICE_ACCESS   | 用户或板级验证角色                           | E2               | hardware validation       |
| SHARED_INFRASTRUCTURE_CHANGE | WRITE                    | Integration Reviewer                         | E3               | dependent regression      |
| BASELINE_CHANGE              | 重新绑定                 | 原验证角色                                   | 重新评估         | evidence validity         |

纵向样板只需落实涉及的条目。

---

# 18. Handoff 契约

Subagent 不依赖完整聊天记录交接。

最小公共内容：

- 任务目标；
- 分类；
- 工作范围；
- 授权；
- Baseline；
- 输入来源；
- Claim；
- Evidence；
- Artifact；
- 已执行动作；
- 当前结论；
- 风险；
- Blocker；
- 下一步。

## 18.1 Context Package

分为：

```text
MUST_HAVE
USEFUL
EXCLUDED
```

必须记录：

- 来源；
- 相关性；
- 新鲜度；
- 失效条件；
- 大小预算。

Context Package 主要是引用和必要摘要，不复制完整历史。

## 18.2 Handoff Acceptance

下游接收 Handoff 时，必须记录：

- 接受者；
- 接受范围；
- 接受依据；
- 是否附带条件；
- 是否拒绝；
- 缺失内容。

接收一个包，不代表接受整个技术结论。

---

# 19. 失败恢复规则

| Failure Type           | 默认责任归属          | 默认恢复路径       |
| ---------------------- | --------------------- | ------------------ |
| INPUT_FAILURE          | 上游输入提供者        | 补充输入           |
| TOOL_FAILURE           | Tooling / Environment | 修复工具或更换工具 |
| ENVIRONMENT_FAILURE    | 环境维护者            | 恢复环境           |
| PERMISSION_FAILURE     | 顶层编排器 / 用户     | 请求授权           |
| IMPLEMENTATION_FAILURE | 实现角色              | 重新实现           |
| VERIFICATION_FAILURE   | 实现或调查角色        | 返工或重新调查     |
| CONTRACT_FAILURE       | 上游 Artifact 生产者  | 修正 Handoff       |
| BASELINE_CONFLICT      | 顶层编排器            | 重新绑定 Baseline  |
| EVIDENCE_CONFLICT      | System Investigator   | 设计区分实验       |
| EXTERNAL_DEPENDENCY    | 外部责任方            | 等待、替代或终止   |

工具失败不得被归类为设计失败。

验证失败不得被实现者自测覆盖。

证据冲突不得被静默忽略。

---

# 20. 关闭门禁模型

不通过增加大量“部分关闭状态”表达复杂情况。

采用 Closure Gate 集合。

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

每个 Gate 包含：

```text
required
status
basis
evidence
accepted_by
conditions
```

Gate Status：

```text
NOT_REQUIRED
UNSATISFIED
SATISFIED
WAIVED
```

`WAIVED` 必须有明确风险接受主体和理由。

顶层 Closure：

```text
OPEN
→ 所有必要 Gate SATISFIED 或合法 WAIVED
→ CLOSABLE
→ 执行关闭
→ CLOSED
```

可以显示：

```text
5 / 7 required gates satisfied
```

但不得把进度比例误认为任务已关闭。

---

# 21. 并发与共享工作区

冻结以下语义：

1. 两个写角色不能同时修改同一受控范围；
2. 多个只读角色可以并行；
3. 验证绑定明确实现版本；
4. 上游变化使旧验证失效或降级；
5. 合并冲突不得静默处理；
6. 用户未提交修改必须保护；
7. 并行产物合并前必须检查范围和 Baseline。

具体使用 worktree、分支还是独立目录，留给平台适配阶段。

---

# 22. 仓库原生项目发展记录

原 `ai-plat-bridge` 拆解重构为仓库原生记录能力。

记录类型：

- Project Status
- Task Record
- Investigation Record
- Decision Record
- Verification Record
- Knowledge Record
- Change/Event Log

## 22.1 Canonical Source Map

| 信息           | 权威来源             |
| -------------- | -------------------- |
| 当前代码内容   | Git 工作树或 commit  |
| 当前执行状态   | Runtime Task State   |
| 跨会话任务状态 | Task Record          |
| Bug 根因状态   | Investigation Record |
| 设计选择       | Decision Record      |
| 当前验证结果   | Verification Package |
| 长期验证摘要   | Verification Record  |
| 当前项目摘要   | Project Status       |
| 可复用知识     | Knowledge Record     |

## 22.2 Project Status

Project Status：

- 只是投影；
- 不参与状态变更；
- 不创造事实；
- 不覆盖底层记录；
- 必须反向引用权威来源。

## 22.3 最小关系语义

```text
DERIVED_FROM
SUPERSEDES
INVALIDATES
VERIFIED_BY
RELATED_TO
```

---

# 23. 克制读写

## 23.1 默认不读取

普通解释、小范围代码阅读、简单工具执行不读取项目历史。

## 23.2 分层读取

```text
L0：路由索引
L1：当前状态
L2：指定任务、调查、决策或验证
L3：原始证据和完整历史
```

必须从最低足够层级开始。

## 23.3 默认写入

默认模式：

```text
发现高价值事件
→ 建议记录
→ 用户确认
→ Documenter 写入
```

目标授权模式：

```text
达到记录门槛
→ 自动压缩、去重、来源检查
→ 写入
→ 写后验证
```

## 23.4 不记录

通常不记录：

- 文件阅读流水；
- 普通命令过程；
- 可由 Git diff 恢复的微小修改；
- 无长期价值的猜测；
- 重复事实；
- 大段代码；
- 完整日志；
- 原始波形；
- 普通知识问答。

---

# 24. 平台中立最小接口

## 24.1 Task Interface

- 创建；
- 分类；
- 更新执行状态；
- 设置接受状态；
- 设置关闭状态；
- 建立依赖；
- 标记 Blocker；
- 恢复任务。

## 24.2 Agent Invocation Interface

- 指定角色；
- 指定范围；
- 指定权限；
- 指定 Baseline；
- 提交 Handoff；
- 接收 Artifact、Evidence、Claim 和失败结果。

## 24.3 Artifact Interface

- 注册；
- 查询；
- 建立依赖；
- 标记版本；
- 标记失效。

## 24.4 Evidence Interface

- 注册；
- 绑定 Baseline；
- 设置 Reproducibility Level；
- 设置 relevance 和 coverage；
- 标记有效或失效。

## 24.5 Claim Interface

- 创建 Claim；
- 关联支持证据；
- 关联反证；
- 更新 Claim 状态；
- 查询某 Gate 依赖的 Claim。

## 24.6 Approval Interface

- 请求权限；
- 描述风险；
- 记录授权范围；
- 检查越权；
- 触发重新审批。

## 24.7 Closure Interface

- 创建 Gate；
- 更新 Gate；
- 记录接受主体；
- 计算 CLOSABLE；
- 执行关闭。

## 24.8 Record Interface

- 按需读取；
- 持久化 Runtime Event；
- 更新权威记录；
- 更新 Project Status；
- 写后验证。

---

# 25. 纵向样板

样板继续采用：

> QSPI 数据拼接异常的调查、修复和验证闭环。

建议流程：

```text
用户目标
→ Task Classification
→ 执行模式判定
→ 建立 Runtime Task
→ 绑定 Baseline
→ 最小上下文读取
→ System Investigator
→ Investigation Package
→ Claim 与 Evidence 注册
→ Verification Engineer 构建复现
→ 处理 Evidence Conflict
→ 请求 WRITE
→ RTL Engineer 修复
→ Artifact 与 Claim 注册
→ Verification Engineer 独立验证
→ Evidence 绑定新 Baseline
→ Integration Reviewer 审查
→ Closure Gate 计算
→ 用户风险接受（如需要）
→ CLOSED
→ Documenter 持久化记录
```

样板必须验证：

- 三轴状态；
- Runtime 与 Task Record 同步；
- 风险变化重评估；
- Artifact 注册门槛；
- Evidence Reproducibility；
- Claim 链路；
- Handoff Acceptance；
- Blocker 恢复；
- Evidence 失效传播；
- Closure Gate；
- 克制读写。

---

# 26. 架构不变量

1. `develoip-copilot` 是能力套件，不是巨型 Skill。
2. 顶层编排器不承担复杂专业实现。
3. DIRECT 模式不得修改正式设计代码。
4. Subagent 对完整专业结果负责。
5. Skill 只承载稳定方法。
6. Tool 负责确定性执行。
7. 每个任务必须显式分类。
8. 每个任务必须具有 Execution Status。
9. Acceptance 与 Closure 必须独立建模。
10. FINISHED 不等于 ACCEPTED。
11. ACCEPTED 不等于 CLOSED。
12. 风险变化必须触发重新评估。
13. 执行模式在风险增加时只能升级。
14. 任何角色不得自行扩大范围或权限。
15. READ、EXECUTE、WRITE、设备访问和破坏性操作必须区分。
16. 高风险修改必须独立验证或审查。
17. 实现者自测不能覆盖独立验证失败。
18. Artifact、Evidence 和 Claim 必须显式区分。
19. Claim 必须关联支持证据或明确标记无证据。
20. 有效反证不得被静默忽略。
21. Evidence 必须绑定 Baseline。
22. E3 不自动等于证据充分。
23. 上游变化必须触发依赖证据和 Claim 重评估。
24. Subagent 通过结构化 Handoff 交接。
25. Handoff 接收不等于技术接受。
26. 任何接受必须记录主体、范围和依据。
27. 工具失败与工程失败必须区分。
28. BLOCKED 必须包含恢复条件。
29. 验证失败阻止相关 Closure Gate。
30. Closure 必须由 Gate 决定。
31. Runtime 是执行期状态操作权威。
32. Task Record 是跨会话持久化权威。
33. Project Status 不得成为事实权威。
34. 两个写角色不得同时修改同一受控范围。
35. 验证必须针对明确实现版本。
36. 合并冲突不得静默处理。
37. 项目记录默认不读、默认不写。
38. Bug 调查必须独立建模。
39. 领域 Subagent 不直接随意维护长期记录。
40. 平台适配不得改变平台中立契约语义。
41. 第一阶段只承诺任务级编排。
42. 未经样板验证的实现细节不得伪装成冻结契约。

---

# 27. Milestone 1.5：统一执行契约

下一阶段只产出一份统一的：

```text
execution-contract.md
```

内部包含：

1. Object Model
2. Event Model
3. Three-axis State Model
4. Risk Policy Matrix
5. Artifact–Evidence–Claim Model
6. Approval Model
7. Failure Recovery Matrix
8. Closure Gate Model
9. Runtime Persistence Model
10. Core Invariants

不应拆成彼此独立、重复定义概念的六套规范。

可以按章节分文件维护，但必须有一个唯一对外契约入口。

---

# 28. 最终判定

v1.2 已从：

> 多 Agent 职责蓝图

升级为：

> 具备显式任务分类、三轴状态、权限决策、证据主张链、失败恢复和关闭门禁的工程 Agent 控制架构。

核心链路为：

```text
Task Classification
→ Runtime Control
→ Agent Execution
→ Artifact
→ Evidence
→ Claim
→ Acceptance
→ Closure Gate
→ Persistent Record
```

下一步不应继续增加角色或抽象层。

应进入 Milestone 1.5，将本蓝图转化为一份最小、统一、可测试的 `execution-contract.md`。
