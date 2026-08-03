# develoip-copilot 设计约束检查表

> 文档用途：所有开发、代码评审和架构决策的第一检查项
> 适用对象：实施者、代码评审者、架构决策者
> 更新频率：仅当 design.md 正式更新时同步更新

---

## 设计不变量 (Design Invariants)

以下十条为 develoip-copilot v2.1 的核心架构语义，未经正式评审不得改变。

### 1. 不创建主控 Agent

**设计依据**：design.md §5.3

**禁止行为**：
- ❌ 创建 `.omp/agents/orchestrator.md`
- ❌ 创建 `.omp/agents/main-controller.md`
- ❌ 创建 `.omp/agents/workflow-runner.md`
- ❌ 任何形式的独立协调 Agent

**正确行为**：
- ✅ 使用 OMP 主会话协调
- ✅ 使用 Skill Procedure 描述流程
- ✅ 使用 `task` 工具调用专业 Agent

---

### 2. 顶层 Skill 对应用户任务

**设计依据**：design.md §6

**禁止行为**：
- ❌ 为每个内部微方法注册顶层 Skill（如 `extract-port`、`parse-clock`）
- ❌ 将底层工具注册为顶层 Skill
- ❌ 要求用户手动组合多个底层 Skill

**正确行为**：
- ✅ 顶层 Skill 直接对应一类用户目标（如 `rtl-to-testbench`）
- ✅ 细粒度方法放入 Skill 的 `references/` 目录
- ✅ OMP 自动匹配最接近用户最终产物的 Skill

---

### 3. 多 Agent 流程写入 Skill Procedure

**设计依据**：design.md §1.1 #2, §7.4

**禁止行为**：
- ❌ 创建独立 Workflow Recipe
- ❌ 创建 `workflows/` 目录
- ❌ 在 Skill 外部定义流程 DSL

**正确行为**：
- ✅ 将多 Agent 流程写入 Skill 的 `Procedure` 章节
- ✅ Procedure 描述完整执行顺序（上下文收集、Agent 调用、工具调用、结果核验、用户确认、产物生成）
- ✅ Skill 不主动执行工具，而是指导 OMP 主会话调度

---

### 4. 专业角色实现为 `.omp/agents/*.md`

**设计依据**：design.md §8

**禁止行为**：
- ❌ 在其他位置定义 Agent 配置
- ❌ 通过代码动态生成 Agent 配置
- ❌ 将 Agent 配置放在 Skill 内部

**正确行为**：
- ✅ develoip-copilot 的所有项目级自定义 Agent 配置位于 `.omp/agents/*.md`
- ✅ 通过 OMP `task` 工具调用
- ✅ Agent 配置稳定可审计

---

### 5. 确定性能力首选独立 Python CLI

**设计依据**：design.md §10

**禁止行为**：
- ❌ 直接在 Skill 中执行复杂计算逻辑
- ❌ 要求模型推断可通过代码稳定完成的操作
- ❌ 将所有工具立即注册为 OMP Custom Tool

**正确行为**：
- ✅ 扫描、解析、编译、仿真等操作通过 Python CLI 完成
- ✅ 工具首先作为独立 Python CLI 实现
- ✅ CLI 可脱离 OMP 独立运行和测试

---

### 6. Python CLI 不强制注册为 Custom Tool

**设计依据**：design.md §10.8

**禁止行为**：
- ❌ 首版就大规模注册 Custom Tool
- ❌ 将所有 Python CLI 强制要求注册
- ❌ 在工具未在真实案例中使用前就注册

**正确行为**：
- ✅ 首版大部分工具通过 `bash` 调用
- ✅ 仅在高频调用、参数复杂、输出需稳定格式时考虑注册
- ✅ Custom Tool 是可选的、按需的升级

---

### 7. Agent 输出引用只用于临时交接

**设计依据**：design.md §9.2-9.3

**禁止行为**：
- ❌ 将 Agent 输出引用作为长期事实源
- ❌ 依赖 Agent 会话持久性
- ❌ 用 Agent 输出引用替代文件系统

**正确行为**：
- ✅ Agent 输出引用仅用于当前会话临时交接
- ✅ 正式工程产物必须写入文件系统
- ✅ 长期项目状态必须写入 `.project/`

---

### 8. 正式产物写入文件系统，长期状态写入 `.project/`

**设计依据**：design.md §11.2-11.4

**禁止行为**：
- ❌ 只在 Agent 输出引用中保留正式产物
- ❌ 依赖 OMP 会话记忆保存工程结论
- ❌ 用隐式状态替代显式文件记录

**正确行为**：
- ✅ Testbench、设计文档、调查报告等必须写入项目目录
- ✅ 长期项目状态统一写入 `.project/`
- ✅ `.project/` 是供人和 Agent 阅读的轻量工程记录，不是 Runtime 数据库

---

### 9. 首版不默认使用 Hub

**设计依据**：design.md §9.5

**禁止行为**：
- ❌ 将 Hub 作为默认协作机制
- ❌ 在串行/并行场景下引入 Hub
- ❌ 为未来可能需求提前设计 Hub 扩展点

**正确行为**：
- ✅ 首版使用串行或并行主会话调度
- ✅ Agent 输出引用用于临时交接
- ✅ 只有在真实案例中证明无法通过主会话调度解决时才考虑 Hub

---

### 10. 不重新引入通用平台能力

**设计依据**：design.md §3, §20

**禁止行为**：
- ❌ 重新引入 Runtime、Event Store、Gate Engine
- ❌ 重新引入 Approval、Acceptance、Waiver 对象系统
- ❌ 重新引入通用任务状态机
- ❌ 重新引入 Snapshot Replay

**正确行为**：
- ✅ 复用 OMP 原生编排能力
- ✅ 复用 OMP 原生确认机制（`ask` 工具）
- ✅ 复用 OMP 原生隔离能力（worktree）
- ✅ 每个技能独立验证，不建设通用平台

---

## 快速检查清单

每次开发或评审时回答以下问题：

### 架构层检查

- [ ] 未新增主控 Agent
- [ ] 未新增独立 Workflow 层
- [ ] 未引入新的通用 Runtime 对象
- [ ] 未把内部方法错误注册成顶层 Skill
- [ ] 未绕过 OMP 原生能力重复造轮子

### 数据流检查

- [ ] 未将临时 Agent 输出当作长期事实源
- [ ] 正式产物已写入文件系统
- [ ] 长期状态已写入 `.project/`
- [ ] 未依赖 Agent 会话持久性

### 工具实现检查

- [ ] 可通过代码完成的操作已交给工具，而非模型
- [ ] Python CLI 可独立运行
- [ ] 未在工具未验证前就大量注册 Custom Tool

### 协作机制检查

- [ ] 未默认使用 Hub
**注意**：
- 不适用项标记为 `N/A` 并简述原因
- 不得为了全部勾选而创建无必要产物或隔离流程
- 例如：纯只读任务可能不写入 `.project/`，标记为 N/A

---

## 使用说明

- [ ] 未绕过用户确认
- [ ] 未绕过工作区隔离
- [ ] 未自动执行 commit、push、merge
- [ ] 未自动访问外部设备

---

## 违规处理

### 违规严重度定义

**轻度**：
- 不改变设计语义
- 只影响路径、命名、字段或内部实现
- 记录在 `docs/design-deviations.md`
- 不影响核心架构语义

**中度**：
- 改变组件职责、调用边界或当前 Milestone 范围
- 暂停实施
- 记录在 `docs/design-deviations.md`
- 必须说明对现有设计的影响
- 判断是否需要更新 design.md

**重度**：
- 改变十条设计不变量中的任意一条
- 立即停止实施
- 记录在 `docs/design-deviations.md`
- 必须正式评审并更新 design.md
- 不得通过偏差记录绕过架构约束

---

## 使用说明

### 开发前

1. 阅读本检查表
2. 确认任务与 design.md 的对应章节
3. 确认不会违反十条设计不变量

### 代码评审前

1. 运行快速检查清单
2. 检查是否存在违反设计不变量的代码
3. 检查是否引入了未计划的架构层

### 架构决策前

1. 评估决策对十条设计不变量的影响
2. 如需偏离，记录在 `docs/design-deviations.md`
3. 重度偏离必须正式评审并更新 design.md

---

## 版本

- v1.1: 2026-08-03, 修复内容损坏，恢复完整十条不变量，补充严重度定义
- v1.0: 2026-08-03, 基于 design.md v2.1 冻结版本初始化