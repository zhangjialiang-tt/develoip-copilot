# develoip-copilot Milestone 3 执行计划

> 里程碑名称：OMP-Native Real Project Pilot
> 中文定位：OMP 原生执行与真实 FPGA 工程试点
> 前置状态：Milestone 2 — `EXECUTED / FROZEN`
> 开发分支：`base/develop`
> 执行平台：OMP/pi
> 计划状态：`IN PROGRESS`（2026-08-03 用户授权，自 Batch 1 起）
> 语义权威：`docs/execution-contract.md`
> 计划文件：`docs/develoip-copilot-Milestone3执行计划.md`

---

# 1. 里程碑决议

从 Milestone 3 开始，`develoip-copilot` 后续开发统一在 OMP/pi 中执行。

执行职责冻结如下：

```text
OMP/pi
= 用户交互入口
+ 主 Agent 运行环境
+ 专业 Subagent 调度环境
+ Tool / Extension / Hook 承载平台

Python Runtime
= Task、Command、Event、Approval、Evidence、Claim、
  Gate、Persistence 和 Restore 的唯一操作权威

Milestone 3 Plan
= 阶段目标、门禁和验收基线

Skill
= 执行方法和行为约束

Codex
= 可选外部代码评审者
```

Codex 不再作为：

- Milestone 计划执行入口；
- Runtime 状态权威；
- 主工程修改 Agent；
- OMP 角色编排器；
- 项目恢复入口。

Codex 只允许用于：

- 独立代码评审；
- 契约偏差评审；
- CI 失败的补充分析；
- 最终冻结前的挑战评审。

---

# 2. 核心原则

## 2.1 Markdown 计划不能直接充当运行时

OMP 不得仅通过读取本计划，自由判断：

- 当前执行到哪个 Batch；
- 哪个 Gate 已满足；
- 是否已经获得 WRITE Approval；
- 某个 Claim 是否成立；
- Task 是否可以关闭。

真实执行进度必须由：

```text
Runtime Task
Runtime Event
Approval
Blocker
Closure Gate
```

共同决定。

计划文档只定义应达到什么结果，不是第二套状态源。

## 2.2 OMP 不得保存第二套 Task 状态

以下内容不得作为权威状态：

- OMP Session 历史；
- Agent Todo；
- Skill 内的阶段清单；
- OMP Memory；
- 对话中的“已经完成”声明；
- Extension 本地缓存；
- Project Status Markdown。

OMP 重启或会话切换后，必须从 Python Runtime 恢复。

## 2.3 Skill、Tool、Extension 分工

OMP 当前的 Skill 是静态方法和上下文，不是可执行 Runtime；模型需要直接调用代码时应使用 Custom Tool；Extension/Hook 负责命令注册、生命周期处理和工具调用拦截。

冻结分工：

```text
Skill
→ 告诉 Agent 应如何执行

Custom Tool
→ 调用 Python Runtime 和 Workspace Adapter

Extension
→ 注册命令、维护桥接进程、处理会话生命周期

Hook
→ 拦截 edit/write/bash 等潜在越权动作

Runtime
→ 决定动作是否合法并产生事实
```

## 2.4 双重安全门禁

OMP 的工具 Approval 与 develoip-copilot Runtime Approval 是两种不同机制。

```text
OMP Tool Approval
= 平台层用户确认

Runtime Approval
= 工程语义授权
```

WRITE 操作必须同时满足：

```text
OMP 允许调用该 Tool
AND
Runtime 中存在有效 Approval
AND
Scope 匹配
AND
Baseline 匹配
AND
无活动阻塞条件
```

OMP 的一次“允许”不能自动生成 Runtime Approval。

---

# 3. Milestone 3 总目标

Milestone 3 必须证明：

> 真实 OMP 主 Agent 和专业 Subagent 能够在真实 FPGA 工程仓库中，通过 develoip-copilot Runtime 完成调查、受控修改、独立验证、恢复和记录闭环。

完整链路：

```text
用户在 OMP 中启动 Milestone 3
→ OMP Extension 连接 Python Runtime
→ Runtime 创建 Task
→ Workspace Adapter 捕获真实 Baseline
→ OMP 调用 System Investigator
→ Runtime 注册 Evidence / Claim
→ OMP 调用 Verification Engineer
→ Risk 重新评估
→ 用户在 OMP 中批准 WRITE
→ 隔离工作区调用 RTL Engineer
→ 独立 Verification Engineer 验证
→ Integration Reviewer Acceptance
→ Runtime 计算 Closure Gate
→ Runtime 持久化
→ OMP 会话重启后恢复
→ Engineering Documenter 处理长期记录
```

---

# 4. 成功定义

Milestone 3 完成时，系统至少能够：

1. 在 OMP 中启动、查询、暂停和恢复 Task；
2. 通过 OMP Custom Tool 调用 Python Runtime；
3. 在 OMP Session 重启后恢复相同 Runtime 状态；
4. 拦截未经授权的 `edit`、`write` 和具有写副作用的 `bash`；
5. 通过 OMP `task` 子代理执行至少三个真实专业角色；
6. 接入一个真实 FPGA Git 工程；
7. 保护用户原工作区和未提交修改；
8. 捕获真实 Git、配置、工具和输入 Baseline；
9. 完成一次只读调查；
10. 完成一次明确授权的隔离 RTL 修改；
11. 完成一次独立验证；
12. 处理一次验证失败或 Evidence Conflict；
13. 处理 Approval 撤销；
14. 处理执行期间 Baseline 变化；
15. 通过 Handoff 支持跨 Agent 和跨会话继续；
16. 形成最小长期工程记录；
17. 未执行板级验证时，不声称真实硬件问题完全关闭。

---

# 5. 冻结输入

Milestone 3 以以下内容为冻结输入：

```text
docs/execution-contract.md
docs/contract-test-scenarios.md
docs/qspi-contract-walkthrough.md
docs/milestone2-decisions.md
docs/milestone2-validation-report.md

runtime/
roles/
tools/
adapters/
tests/
```

执行开始时记录：

```text
milestone2_frozen_commit
omp_version
bun_version
python_version
pytest_version
operating_system
```

OMP 的 Extension、Tool、Hook 和 Skill 接口可能随版本变化，因此必须固定本里程碑使用的 OMP 版本，并为版本升级设置兼容性回归。

---

# 6. 执行工作目录

OMP 主会话固定从：

```text
develoip-copilot 仓库根目录
```

启动。

原因：

- 项目级 `.omp/` 配置只对当前工作目录生效；
- Skill、Custom Tool 和 Extension 应由 develoip-copilot 项目管理；
- 真实试点仓库通过 Workspace Adapter 作为外部工程接入；
- 试点工程不承担 develoip-copilot 平台配置。

运行关系：

```text
develoip-copilot/
  ├─ Runtime
  ├─ OMP Extension
  ├─ OMP Skills
  └─ Workspace Adapter
          │
          ▼
external pilot FPGA repository
```

---

# 7. 本阶段不做什么

Milestone 3 不包含：

- 完整 OMP 插件市场发布；
- 通用工作流 DSL；
- Web Dashboard；
- 多项目并行管理；
- 多用户权限系统；
- 自动 Git commit；
- 自动 push；
- 自动创建或合并 PR；
- 真实板卡烧写；
- 自动固件升级；
- 自动设备复位；
- Firmware Engineer 完整纵向样板；
- Algorithm Engineer 完整纵向样板；
- 任意自定义 Runtime 状态机；
- 将 Runtime 重写为 TypeScript；
- 将 OMP Session 变成第二事实源。

---

# 8. 实现组成

Milestone 3 最小新增以下组件。

## 8.1 OMP Project Skill

建议位置：

```text
.omp/skills/develoip-copilot/SKILL.md
```

负责：

- 识别何时使用 develoip-copilot；
- 要求所有正式动作经过 Runtime；
- 告诉主 Agent 如何查询 Task；
- 告诉主 Agent如何创建 Handoff；
- 约束角色职责；
- 说明 Approval、Baseline 和 Scope 规则；
- 说明何时必须停止并请求用户决策。

Skill 不得：

- 自己保存 Task 状态；
- 宣布 Gate 已满足；
- 直接授予 WRITE；
- 替代 Runtime Query；
- 自动把自然语言结论写成 FACT。

OMP 的原生项目 Skill 按 `.omp/skills/<name>/SKILL.md` 发现，且 Skill 主要用于模型可读的方法和上下文。

## 8.2 OMP Extension Package

建议结构：

```text
omp-extension/develoip-copilot/
├─ package.json
└─ src/
   ├─ index.ts
   ├─ bridge.ts
   ├─ commands.ts
   ├─ tools.ts
   ├─ guards.ts
   ├─ session.ts
   └─ renderers.ts
```

Extension 负责：

- 启动和维护 Python Bridge；
- 注册 OMP 命令；
- 注册或装配 Custom Tool；
- 监听 Session 生命周期；
- 拦截敏感 Tool 调用；
- 显示 Task、Approval、Blocker 和 Gate 摘要；
- OMP 重启时触发 Runtime Restore。

Extension 物理加载方式在 Batch 1 通过当前固定 OMP 版本验证后冻结，可采用：

- Extension discovery；
- package manifest；
- linked plugin；
- SDK `additionalExtensionPaths`。

不得同时维护多套加载路径作为正式入口。

## 8.3 Python OMP Bridge

新增建议：

```text
runtime/omp_bridge.py
runtime/omp_protocol.py
```

启动入口：

```text
python -m runtime.omp_bridge --stdio
```

通信采用 newline-delimited JSON：

```text
stdin:
  request JSON

stdout:
  response JSON
  event notification JSON
```

最小操作：

```text
hello
dispatch
query
restore
save_snapshot
invoke_role_result
workspace_status
health
shutdown
```

Bridge 只负责协议转换。

它不得：

- 绕过 `Runtime.dispatch()`；
- 直接修改对象；
- 直接写 Derived Result；
- 将 OMP Session 历史导入 Runtime 作为事实；
- 在错误时产生部分成功 Event。

## 8.4 OMP Custom Tools

项目级 Custom Tool 可由 `.omp/tools` 或正式 Extension 注册；Custom Tool 是 OMP 中可被模型调用、具有参数 Schema 和副作用的执行接口。

最小工具：

```text
dc_dispatch
dc_query
dc_invoke_role
dc_submit_candidates
dc_workspace_status
dc_capture_baseline
dc_restore
dc_record
```

### dc_dispatch

提交合法 Runtime Command。

### dc_query

读取 Task、对象、Blocker、Approval 和 Gate。

### dc_invoke_role

通过 OMP `task` 调用专业 Subagent。

### dc_submit_candidates

将专业角色输出转换为候选 Runtime Command。

### dc_workspace_status

查询外部试点仓库和隔离工作区状态。

### dc_capture_baseline

捕获真实工程 Baseline。

### dc_restore

恢复 Runtime 和当前 Task。

### dc_record

提交长期 Record 候选或 record gate 决策。

## 8.5 OMP Commands

最小用户命令：

```text
/dc doctor
/dc m3-start
/dc status
/dc resume
/dc approve
/dc reject
/dc revoke
/dc pause
/dc cancel
/dc close
```

### /dc doctor

检查：

- OMP 版本；
- Python；
- Bridge；
- Runtime；
- Event Store；
- Extension；
- Custom Tools；
- Skill；
- 试点仓库；
- Git；
- 隔离能力。

### /dc m3-start

创建 Milestone 3 顶层 Task，不直接开始 WRITE。

### /dc status

显示：

- Task；
- Execution Status；
- Baseline；
- Approval；
- Blocker；
- 当前角色；
- 下一合法动作；
- Gate。

### /dc resume

从 Runtime Event Store 恢复，不从聊天记录推断。

### /dc approve / reject / revoke

必须显示：

- Capability；
- Scope；
- Risk；
- Baseline；
- 申请角色；
- 保留 Gate。

## 8.6 Tool Guard

Extension/Hook 必须拦截：

```text
edit
write
ast_edit
bash
```

判定逻辑：

```text
调用是否可能产生写副作用
→ 查询当前 Runtime Task
→ 查询有效 Approval
→ 检查 Scope
→ 检查 Baseline
→ 检查 Blocker
→ 允许或拒绝
```

Extension 支持注册 Tool Hook 和命令，适合实现调用前后的控制逻辑。

禁止只依赖模型提示：

> “请不要未经授权修改文件。”

WRITE 防护必须是程序化门禁。

---

# 9. OMP 专业角色

Milestone 3 首批 OMP 角色：

```text
dc-orchestrator
dc-system-investigator
dc-rtl-engineer
dc-verification-engineer
dc-integration-reviewer
dc-engineering-documenter
```

OMP 的 `task` 工具支持子代理调度及 worktree、overlay 等隔离机制；Milestone 3 应复用该能力，而不是自行实现另一套子进程 Agent 框架。

## 9.1 Orchestrator

允许：

- 创建和分类 Task；
- 激活 Risk；
- 选择角色；
- 创建 Handoff；
- 请求 Approval；
- 请求 Closure。

禁止：

- 修改 RTL；
- 自行验证；
- 签发 Waiver；
- 直接设置 Gate。

## 9.2 System Investigator

允许：

- READ；
- SAFE_EXECUTE；
- Evidence Candidate；
- Observation / Hypothesis；
- Risk Proposal；
- Blocker Proposal。

禁止：

- 正式修改代码；
- 将 Hypothesis 原地升级为 FACT；
- 接受自己的 Claim。

## 9.3 RTL Engineer

允许：

- 授权 Scope 内 WRITE；
- 局部自测；
- Artifact Candidate；
- Implementation Handoff。

禁止：

- 修改原生产工作区；
- 扩大 Scope；
- 独立接受自己的结果；
- 声称板级问题关闭。

## 9.4 Verification Engineer

允许：

- 独立复现；
- 回归；
- Evidence Candidate；
- 反证；
- Verification Blocker。

禁止：

- 修改被验证实现；
- 将测试通过等同于整体关闭；
- 覆盖失败结果。

## 9.5 Integration Reviewer

允许：

- 技术 Acceptance；
- 拒绝或条件接受；
- Coverage 审查；
- Gate 充分性建议。

禁止：

- 修改 RTL；
- 签发用户 Waiver；
- 直接设置 Closure。

## 9.6 Engineering Documenter

允许：

- Record Candidate；
- 去重；
- 引用校验；
- record gate 处置。

禁止：

- 创建工程结论；
- 改变 Task 状态；
- 修改 Claim Status；
- 创建 Closure Event。

---

# 10. 角色输出协议

所有 OMP 专业角色必须输出：

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

禁止字段：

```text
gate_status
claim_status
closure_status
project_status
approval_granted
task_closed
```

角色输出只是 Proposal。

正式生效链路：

```text
OMP Role Output
→ RoleInvocationLayer 校验
→ dc_submit_candidates
→ Runtime Command
→ Domain Event
→ Derived Result 重算
```

非结构化输出不能直接成为权威对象。

---

# 11. 六个执行 Batch

```text
Batch 1：OMP Execution Harness
Batch 2：真实 Workspace 与 Baseline
Batch 3：OMP 专业角色集成
Batch 4：只读调查闭环
Batch 5：受控修改与独立验证
Batch 6：恢复、记录与价值评估
```

---

# 12. Batch 1：OMP Execution Harness

## 12.1 目标

让 OMP 成为 Milestone 3 的真实执行入口。

## 12.2 工作项

### 固定 OMP 技术基线

记录：

```text
omp_version
bun_version
extension_loading_method
custom_tool_loading_method
skill_discovery_method
task_isolation_mode
tool_approval_policy
```

### 建立 Skill

实现项目级 `develoip-copilot` Skill。

### 建立 Extension

实现：

- Bridge 生命周期；
- `/dc` 命令；
- Runtime 状态显示；
- Tool Guard；
- Session start/switch/shutdown 处理。

### 建立 Python Bridge

实现：

- JSONL 协议；
- request ID；
- timeout；
- cancellation；
- stderr 日志隔离；
- crash restart；
- Runtime Restore；
- health check。

### 建立 Custom Tools

实现：

```text
dc_dispatch
dc_query
dc_restore
dc_invoke_role
dc_submit_candidates
```

### 建立状态视图

OMP 只显示 Runtime Query 结果，不自行计算：

- Task；
- Approval；
- Blocker；
- Gate；
- 下一合法动作。

## 12.3 Gate A：OMP 执行入口门禁

进入 Batch 2 前必须满足：

1. OMP 可发现项目 Skill；
2. OMP 可加载 Extension；
3. `/dc doctor` 通过；
4. OMP 可启动 Python Bridge；
5. `dc_query` 可读取 Runtime；
6. `dc_dispatch` 可创建 Task；
7. `/dc resume` 可恢复 Event Store；
8. OMP Session 不保存第二套状态；
9. Derived Result 写入被拒绝；
10. 未授权 `edit/write/bash` 被拦截；
11. Bridge 崩溃后可恢复；
12. Milestone 2 Adapter tests 保持通过。

---

# 13. Batch 2：真实 Workspace 与 Baseline
真实Workspace：C:\100-Working\102-Working-Prj\ptrw038\2
真实rtl：C:\100-Working\102-Working-Prj\ptrw038\2\common\rtl\dev\qspi_flash

## 13.1 目标

安全接入真实 FPGA 工程，不修改用户原工作区。

## 13.2 试点输入

启动前必须提供：

```text
pilot_repository
pilot_branch_or_commit
pilot_problem
read_scope
candidate_write_scope
existing_test_entry
toolchain
input_data
```

## 13.3 Workspace Adapter

实现：

- Git root 发现；
- branch/commit；
- tracked/untracked；
- modified/ignored；
- submodule；
- relevant file hash；
- 工具版本；
- 输入引用；
- 隔离工作区创建；
- 修改前后 diff；
- Scope 检查。

## 13.4 工作区分类

```text
CLEAN
DIRTY_RELATED
DIRTY_UNRELATED
CONFLICTING
UNKNOWN
```

`UNKNOWN` 和 `CONFLICTING` 状态下禁止 WRITE。

## 13.5 隔离策略

优先使用 OMP `task` 的隔离能力。

首选顺序由当前平台能力决定：

```text
ProjFS / overlay
→ Git worktree
→ 独立临时 clone
```

写入结果以 patch 或隔离分支形式保留，不自动合并回用户工作区。

## 13.6 Gate B：Workspace 门禁

必须满足：

1. 原工作区不被修改；
2. 未提交修改不丢失；
3. Baseline 可重复捕获；
4. Scope 外修改被拒绝；
5. protected path 不可写；
6. 用户相关脏修改被识别；
7. 工具执行副作用可审计；
8. 不执行真实设备操作；
9. 所有 Milestone 2 tests 保持通过。

---

# 14. Batch 3：OMP 专业角色集成

## 14.1 目标

让真实 OMP 子代理承担契约角色，而不是使用测试 Stub。

## 14.2 工作项

- 注册或发现六个 OMP 角色；
- 设置每个角色的 Tool Allowlist；
- 设置读写边界；
- 设置模型和推理强度；
- 设置 Completion Criteria；
- 校验结构化输出；
- 实现 timeout、retry、abort；
- 支持任务隔离；
- 将候选结果提交 Runtime。

## 14.3 最小真实调用

至少完成：

```text
Orchestrator
→ System Investigator
→ Verification Engineer
```

并验证：

- Handoff 正确；
- Baseline 一致；
- 输出满足 Schema；
- Agent 中断可恢复；
- Role 不可直接写状态；
- 子代理不能通过内置 Tool 绕过 Guard。

## 14.4 Gate C：角色集成门禁

必须满足：

1. 至少三个角色由真实 OMP 子代理执行；
2. Role Invocation 不再使用测试 Stub；
3. Tool Allowlist 有效；
4. Investigator 无 WRITE；
5. Engineer 无 Acceptance 权限；
6. Reviewer 无实现权限；
7. Documenter 无状态迁移权限；
8. 非结构化结果不会自动激活；
9. 子代理失败形成正确 Blocker；
10. OMP `task` 隔离结果可回收和审查。

---

# 15. Batch 4：只读调查闭环

## 15.1 目标

在真实 FPGA 工程中完成一次只读调查和复现。

## 15.2 初始能力

```text
READ
SAFE_EXECUTE
```

不得授予 WRITE。

## 15.3 调查路径

```text
创建 INVESTIGATE Task
→ 捕获 Baseline A
→ 构建 MUST_HAVE Context
→ System Investigator
→ Observation / Hypothesis
→ Verification Engineer
→ 最小复现
→ Evidence / Conflict
→ Investigation Handoff
```

## 15.4 Context Package

必须分为：

```text
MUST_HAVE
USEFUL
EXCLUDED
```

并记录：

- 来源；
- 相关性；
- 新鲜度；
- 失效条件；
- 字节或 Token 大小；
- 下游用途。

不得默认加载：

- 整个仓库；
- 全部 Git 历史；
- 全部长期记录；
- 完整 OMP 对话历史。

## 15.5 Evidence Conflict

板级 Observation 与仿真结果不一致时：

```text
EVIDENCE_CONFLICT
→ Blocker
→ 区分性实验
→ Claim 保持未决
```

不得因里程碑压力直接猜测修复。

## 15.6 Gate D：调查门禁

进入 Batch 5 前必须满足：

1. 真实问题定义可复核；
2. Observation 与 Hypothesis 分离；
3. Evidence 绑定 Baseline A；
4. 复现结果明确；
5. 无法复现时形成 Blocker；
6. Handoff 不依赖完整聊天历史；
7. 无有效证据时不产生 FACT；
8. 未发生正式代码修改；
9. 修改候选和 Scope 明确；
10. 用户确认是否进入 WRITE 阶段。

---

# 16. Batch 5：受控修改与独立验证

## 16.1 目标

在 OMP 中完成一次真实、授权、隔离的 RTL 修改和独立验证。

## 16.2 Risk 重评估

修改前重新检查：

```text
PROTOCOL_BEHAVIOR_CHANGE
STORAGE_LAYOUT_CHANGE
CLOCK_RESET_CHANGE
CDC_CHANGE
EXTERNAL_INTERFACE_CHANGE
BASELINE_CHANGE
```

新增 Risk 必须使已有 Approval 重新评估。

## 16.3 OMP Approval 流程

`/dc approve` 必须显示：

```text
task
actor
capability
scope
baseline
risk_factors
allowed_tools
protected_paths
required_validator
retained_gates
```

用户批准后，由 Runtime 产生 Approval Event。

## 16.4 RTL Engineer

在隔离环境中：

- 修改授权文件；
- 注册 Artifact Candidate；
- 执行局部自测；
- 说明影响；
- 说明自测限制；
- 提交 Implementation Handoff。

## 16.5 Baseline B

修改后必须建立新 Baseline。

```text
Baseline A
→ Baseline B
→ A 的 Evidence/Acceptance/Gate 重新评估
→ 新验证绑定 B
```

## 16.6 Independent Verification

Verification Engineer 至少满足：

```text
INDEPENDENT_ROLE
```

并优先满足：

```text
INDEPENDENT_METHOD
```

验证覆盖：

- 正常路径；
- 边界；
- 顺序；
- 长度；
- 握手；
- 原失败用例；
- 错误路径；
- 回归影响。

## 16.7 Integration Review

Reviewer 检查：

- Scope；
- Approval；
- Baseline；
- Artifact；
- Evidence；
- Relevance；
- Coverage；
- Independence；
- 反证；
- 遗留风险；
- Gate。

## 16.8 Gate E：修改与验证门禁

必须满足：

1. 原工作区未修改；
2. 修改未超 Scope；
3. Artifact 绑定 Baseline B；
4. A 的 Evidence 未误用于 B；
5. 实现者自测与独立验证分离；
6. 验证失败能形成反证；
7. 失败时进入 `REWORK_REQUIRED`；
8. Reviewer Acceptance 与 Waiver 分离；
9. Approval 撤销后不能继续写入；
10. 未验证硬件时不声称板级问题关闭。

---

# 17. Batch 6：恢复、记录与价值评估

## 17.1 目标

证明 OMP 会话不是任务生命线，真实任务可以跨会话恢复。

## 17.2 强制中断点

至少在以下位置主动中断 OMP：

- 调查完成后；
- Approval 等待中；
- RTL 修改后；
- 验证失败后；
- Closure 前。

重新启动 OMP 后执行：

```text
/dc resume
```

恢复内容：

- Task；
- Baseline；
- Approval；
- Blocker；
- Handoff；
- Artifact；
- Evidence；
- Claim；
- Acceptance；
- Gate；
- Event sequence。

## 17.3 Session 生命周期

Custom Tool/Extension 可接收 Session start、switch、branch、shutdown 等生命周期事件，应利用这些事件检查 Bridge 和 Runtime 状态，但不能从 Session 历史重建权威状态。

## 17.4 长期记录

最小输出：

```text
Task Record
Investigation Record
Verification Record（有长期价值时）
Project Status projection
```

不保存：

- 全部 OMP 对话；
- 全部 Tool Call；
- 全部 Event Store 副本；
- 全量长日志；
- 每个 Handoff 的完整复制。

## 17.5 价值评估

记录：

```text
OMP 主 Agent 调用次数
Subagent 调用次数
Tool 调用次数
人工 Approval 次数
Context Package 大小
读取文件数量
写入文件数量
越权拒绝次数
Agent 重试次数
调查耗时
修改耗时
验证耗时
恢复耗时
长期 Record 数量
```

定性评估：

- 哪一步最有价值；
- 哪一步最繁重；
- 哪个角色边界不自然；
- 哪个对象没有实际价值；
- 哪些 Tool 值得产品化；
- 哪些 Skill 实际被复用；
- OMP 是否比 Codex 单会话更适合作为执行入口；
- 是否减少了用户手动转交上下文。

## 17.6 Gate F：最终冻结门禁

必须满足：

1. 至少一次真实 OMP 重启恢复成功；
2. Snapshot 与完整 replay 一致；
3. Runtime 与 OMP Session 不双写；
4. Runtime 与长期 Record 不双写；
5. Project Status 仍为只读投影；
6. 用户拒绝长期记录路径通过；
7. Documenter 未创造状态；
8. Milestone 2 全量回归通过；
9. OMP Harness 回归通过；
10. 真实试点价值评估完成；
11. 无未解决 P0 契约偏差。

---

# 18. 必须执行的验收场景

## M3-O01：OMP 未加载 Extension

预期：

- `/dc doctor` 失败；
- 不启动 Milestone 3；
- 不允许退化为纯 Prompt 执行。

## M3-O02：Bridge 崩溃

预期：

- Tool 返回明确失败；
- 不产生部分成功 Event；
- Bridge 重启后从 Event Store 恢复。

## M3-O03：Agent 直接调用 edit

Given：

- Task 无有效 WRITE Approval。

预期：

- Guard 阻止；
- 不修改文件；
- 返回 `APPROVAL_REQUIRED` 或 Scope 错误。

## M3-O04：bash 隐含写操作

例如：

```text
sed -i
python 脚本写文件
git checkout -- file
```

预期：

- Guard 识别潜在副作用；
- 请求审批或拒绝；
- 不允许通过 bash 绕过 write Tool。

## M3-O05：Role 直接返回 Gate 状态

预期：

- RoleInvocationLayer 拒绝；
- 不产生 Gate Event；
- 记录结构化输出错误。

## M3-O06：用户工作区有未提交修改

预期：

- 原工作区不被修改；
- 建立隔离环境；
- 相关修改进入 Baseline 判断；
- 冲突时形成 `BASELINE_CONFLICT`。

## M3-O07：Scope 外写入

预期：

- Tool 调用被拦截；
- 不产生部分 Artifact；
- 需要重新定界和 Approval。

## M3-O08：验证失败

预期：

- 注册反证；
- Claim 不再保持无条件支持；
- Gate `UNSATISFIED`；
- Task `REWORK_REQUIRED`。

## M3-O09：Approval 撤销

预期：

- 后续写入立即停止；
- 已生成 Artifact 保持待审查；
- OMP 原平台允许状态不能覆盖 Runtime 撤销。

## M3-O10：Baseline 变化

预期：

- Evidence 失效或降级；
- Acceptance 重评估；
- Gate 重算；
- 不允许沿用旧验证。

## M3-O11：OMP Session 重启

预期：

- `/dc resume` 恢复；
- 不重复创建 Task；
- 不依赖完整聊天历史；
- Command 重试保持幂等。

## M3-O12：用户拒绝 Record

预期：

- record gate 完成处置；
- 不生成虚假 Record；
- 技术关闭不被无故阻塞。

## M3-O13：未执行硬件验证

预期：

- 只关闭代码/仿真范围内目标；
- 不声明真实板上问题完全解决；
- hardware gate 按顶层 Scope 正确处理。

---

# 19. 测试策略

## 19.1 Python Runtime 回归

```text
python -m pytest -q
python -m compileall -q runtime roles tools adapters fixtures tests
```

## 19.2 OMP Extension Tests

覆盖：

- Extension 加载；
- 命令注册；
- Bridge 生命周期；
- Tool 参数；
- cancellation；
- timeout；
- Tool Guard；
- Session 恢复；
- 状态渲染。

## 19.3 Bridge Contract Tests

覆盖：

- request/response ID；
- 非法 JSON；
- Runtime Error；
- stderr 隔离；
- 幂等；
- Bridge restart；
- Event Store 损坏；
- Schema version 不兼容。

## 19.4 OMP Real Session Tests

不得全部使用模拟 Session。

至少通过真实 OMP 执行：

```text
S03
S06
S13
S20
S24
M3-O03
M3-O08
M3-O11
```

## 19.5 Workspace Tests

覆盖：

- clean；
- dirty related；
- dirty unrelated；
- conflicting；
- untracked；
- protected path；
- out-of-scope write；
- isolation cleanup。

## 19.6 Pilot E2E

至少运行：

- 只读调查；
- 成功修改；
- 验证失败；
- Approval 撤销；
- Baseline 变化；
- Session 中断恢复；
- 拒绝长期记录。

---

# 20. 建议目录结构

```text
develoip-copilot/
├─ .omp/
│  ├─ skills/
│  │  └─ develoip-copilot/
│  │     └─ SKILL.md
│  ├─ tools/
│  └─ config.yml
├─ omp-extension/
│  └─ develoip-copilot/
│     ├─ package.json
│     └─ src/
├─ runtime/
│  ├─ omp_bridge.py
│  └─ omp_protocol.py
├─ workspace/
│  ├─ adapter.py
│  ├─ baseline.py
│  ├─ scope.py
│  └─ isolation.py
├─ roles/
├─ tools/
├─ tests/
│  ├─ omp/
│  ├─ bridge/
│  ├─ workspace/
│  └─ pilot/
└─ docs/
```

物理目录可以在 Batch 1 调整，但不得改变职责边界。

---

# 21. 实现期文档

Milestone 3 最终交付：

```text
docs/develoip-copilot-Milestone3执行计划.md
docs/milestone3-omp-decisions.md
docs/milestone3-validation-report.md
docs/milestone3-pilot-report.md
docs/milestone3-contract-deviations.md
```

## milestone3-omp-decisions.md

记录：

- OMP 版本；
- Extension 加载方式；
- Custom Tool 加载方式；
- Skill 发现方式；
- Bridge 协议；
- Isolation 模式；
- Tool Approval 配置；
- 角色模型分配；
- Timeout/Retry；
- Session Restore。

## milestone3-validation-report.md

记录：

- 起始 commit；
- 冻结 commit；
- OMP 版本；
- 测试命令；
- 自动化结果；
- 真实 OMP Session 证据；
- Workspace Gate；
- Pilot Gate；
- Restore；
- 剩余限制。

## milestone3-contract-deviations.md

任何与冻结契约不一致的行为必须记录。

无偏差时明确：

```text
No known contract deviations
```

---

# 22. 主要风险

## 风险一：OMP 只成为新的聊天入口

控制：

- 状态必须来自 Runtime；
- 关键动作必须调用 Custom Tool；
- Skill 不能代替 Runtime；
- Session 历史不能作为恢复源。

## 风险二：Agent 绕过 develoip-copilot Tool

控制：

- Tool Guard；
- Built-in Tool Approval；
- Runtime Approval；
- Scope 前后校验；
- 原工作区只读。

## 风险三：Extension 变成第二 Runtime

控制：

- Extension 不保存业务对象；
- 只缓存 Bridge 连接；
- 状态视图每次来自 `dc_query`；
- 重启后必须 restore。

## 风险四：OMP API 变化

控制：

- 固定 OMP 版本；
- `/dc doctor`；
- Compatibility tests；
- 升级前先运行 Harness 回归；
- 不自动追随最新版。

## 风险五：子代理名义分离、实际不分工

控制：

- 独立 Tool Allowlist；
- 独立输入输出；
- Investigator 禁止 WRITE；
- Engineer 禁止 Acceptance；
- Reviewer 禁止实现；
- Documenter 禁止状态迁移。

## 风险六：bash 绕过写保护

控制：

- 识别命令意图；
- 拦截潜在写操作；
- 限制工作目录；
- 运行后 diff 校验；
- Scope 外变化回滚并阻塞 Task。

## 风险七：真实工程试点过大

控制：

- 一个仓库；
- 一个问题；
- 一个修改 Scope；
- 不接真实设备；
- 不自动提交和推送。

---

# 23. Milestone 3 冻结条件

只有同时满足以下条件，才能标记：

```text
Milestone 3 — EXECUTED / FROZEN
```

1. OMP 是实际执行入口；
2. OMP Skill、Extension、Custom Tool 均可正常加载；
3. Python Runtime 仍是唯一状态权威；
4. `/dc doctor`、`status`、`resume` 可用；
5. OMP Session 重启后可恢复；
6. `edit/write/bash` 越权防护有效；
7. OMP Approval 与 Runtime Approval 没有混淆；
8. 真实 FPGA 仓库已安全接入；
9. 用户原工作区未被修改；
10. Baseline 可复核；
11. 至少三个专业角色由真实 OMP Subagent 执行；
12. 完成一次真实只读调查；
13. 完成一次授权隔离修改；
14. 完成一次独立验证；
15. 完成一次 Reviewer Acceptance；
16. 至少执行一次验证失败或 Evidence Conflict；
17. Approval 撤销路径通过；
18. Baseline 失效传播通过；
19. Scope 越界写入被拒绝；
20. Handoff 不依赖完整聊天记录；
21. Runtime 与长期 Record 不双写；
22. Project Status 保持只读；
23. 未验证硬件时没有虚假关闭声明；
24. Milestone 2 全量回归继续通过；
25. OMP Harness 回归通过；
26. 无未解决 P0 契约偏差；
27. 真实试点证明 OMP 执行方式具有明确工程价值；
28. Codex 未成为隐藏的主执行依赖。

---

# 24. 状态定义

```text
Milestone 3 — PROPOSED
```

OMP Harness 开始实现：

```text
Milestone 3 — IN PROGRESS
```

OMP 执行入口冻结：

```text
Milestone 3 — OMP HARNESS READY
```

只读调查完成：

```text
Milestone 3 — INVESTIGATION COMPLETE
```

真实修改与验证完成：

```text
Milestone 3 — EXECUTED / PENDING REVIEW
```

契约无法表达真实流程：

```text
Milestone 3 — BLOCKED BY CONTRACT DEFECT
```

全部 Gate 满足：

```text
Milestone 3 — EXECUTED / FROZEN
```

---

# 25. 推荐执行顺序

```text
1. 冻结 Milestone 3 起始 commit
2. 固定 OMP 版本
3. 实现 /dc doctor
4. 实现 Python Bridge
5. 实现 OMP Custom Tools
6. 实现 Extension 与 Tool Guard
7. 实现项目 Skill
8. 通过 Gate A
9. 接入真实试点仓库
10. 通过 Workspace Gate
11. 注册真实 OMP 专业角色
12. 完成只读调查
13. 评审 Investigation Handoff
14. 用户批准 WRITE
15. 隔离修改
16. 独立验证
17. 执行失败、撤销和 Baseline 变化场景
18. 执行 OMP 重启恢复
19. 生成长期记录
20. 生成 Pilot/Validation Report
21. 使用 Codex 或其他独立模型做挑战评审
22. 冻结 Milestone 3
```

---

# 26. 最终判定标准

Milestone 3 的核心不是：

> OMP 是否能够读取并完成一份 Markdown 计划。

而是：

> OMP 是否能够作为真实工程 Agent 运行平台，在不获得第二套状态权威的前提下，调用 develoip-copilot Runtime，约束专业角色、保护工作区、处理失败并恢复真实 FPGA 开发任务。

只有这一点成立，后续开发才继续由 OMP 主导。
