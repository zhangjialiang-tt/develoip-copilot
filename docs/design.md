> 文档状态：FROZEN / BASELINE v2.1
> 冻结日期：2026-08-03
> 修改规则：后续可调整文件名、字段和实现细节，但未经评审不得改变核心架构语义
> 产品形态：面向个人 FPGA/嵌入式工程师的 OMP 原生专业能力套件
> 运行平台：OMP/pi
> 首版实现语言：Python
> 核心原则：复用 OMP 原生编排能力，以用户任务型 Skill 为入口，以专业 Subagent 为执行单元，以确定性工具提供工程能力
---

# 1. 背景

FPGA/嵌入式开发包含多类差异明显的专业任务：

1. 根据现有 RTL 搭建 testbench；
2. 根据接口或算法说明撰写设计方案；
3. 整理 Bug 调查过程和证据链；
4. 维护项目状态、待办和已验证结论；
5. 对比 RTL 与 Python/C++ 参考模型；
6. 分析仿真日志、波形和时序报告；
7. 生成回归测试框架；
8. 梳理模块接口、数据流和时钟域；
9. 调试软核 C 程序和开发外设驱动。

这些任务无法由单个 Skill 或单个 Subagent 高质量完成，但也不需要自建一套通用 Agent Runtime。

`develoip-copilot` 应建立在 OMP 原生能力之上，通过：

```text
用户任务型 Skill
+ 专业 Subagent
+ OMP 主会话调度
+ Python 确定性工具
+ 正式工程产物
```

组合解决真实工程问题。

## 1.1 v1 到 v2.1 的主要变化

1. 删除独立主控 Agent，直接使用 OMP 主会话；
2. 删除独立 Workflow Recipe，流程合并到 Skill 的 Procedure；
3. 删除通用 Runtime、Event Store、Gate 和 Approval 对象；
4. 删除统一任务产物数据库；
5. 目录遵循 `.omp/skills/<name>/SKILL.md` 和 `.omp/agents/*.md`；
6. Agent 输出引用只用于当前任务临时交接；
7. 正式工程产物仍写入文件系统；
8. 长期项目状态写入 `.project/`；
9. Skill 不主动执行工具，而是指导 OMP 主会话调度；
10. 首版不使用 Hub 作为默认协作机制；
11. 项目工具优先实现为独立 Python CLI；
12. Custom Tool 仅作为按需升级；
13. 优先使用 OMP 原生隔离能力，不自建工作区框架；
14. 顶层 Skill 对应用户任务，细粒度方法放入 references；
15. 每个 Skill 必须定义触发、流程、产物、验证和失败处理。

---

# 2. 产品定位

## 2.1 定位

`develoip-copilot` 是一套运行于 OMP/pi 的模块化 FPGA/嵌入式工程能力套件。

它为个人工程师提供：

- RTL 工程理解；
- 设计方案生成；
- 验证环境建设；
- 仿真与时序分析；
- Bug 调查；
- 参考模型一致性检查；
- 回归测试建设；
- 固件与驱动开发；
- 项目状态维护。

系统没有独立于 OMP 的交互入口。

用户始终通过 OMP 主会话提出目标。

## 2.2 用户体验

用户输入：

```text
根据 qspi_driver_new.v 搭建一个自检 testbench。
```

系统执行：

```text
匹配 rtl-to-testbench Skill
→ 读取 Skill Procedure
→ 调用 rtl-analyst
→ 校验接口分析结果
→ 调用 verification-engineer
→ 在隔离环境生成 testbench
→ 执行仿真
→ 必要时调用 simulation-analyst
→ 汇总产物和验证结果
```

用户不需要了解：

- Agent 配置文件；
- Skill 内部 references；
- task 参数；
- Agent 输出引用；
- Python 工具参数；
- 内部上下文交接方式。

---

# 3. 非目标

首版不建设：

- 独立主控 Agent；
- 通用 Agent Runtime；
- Event Store；
- Snapshot Replay；
- 通用任务状态机；
- Approval 对象；
- Acceptance 或 Waiver 对象；
- Closure Gate；
- 独立 Workflow DSL；
- 多用户权限系统；
- Web Dashboard；
- 自动 commit、push 或 merge；
- 自动烧写板卡；
- 自动固件升级；
- 通用跨项目任务调度；
- 长期驻留 Agent 服务；
- 自定义工作区隔离框架。

---

# 4. 总体架构

```text
用户
  │
  ▼
OMP 主会话
  │
  ├── 匹配用户任务型 Skill
  ├── 读取 Skill Procedure
  ├── 调用 task 执行专业 Subagent
  ├── 读取 Subagent 输出
  ├── 调用项目级 Python CLI
  ├── 请求必要的用户确认
  └── 汇总正式工程产物
  │
  ▼
专业 Subagents
  │
  ├── rtl-analyst
  ├── design-architect
  ├── verification-engineer
  ├── simulation-analyst
  ├── debug-investigator
  ├── model-consistency-analyst
  ├── firmware-engineer
  └── project-steward
  │
  ▼
Python Deterministic Tools
  │
  ▼
RTL / Testbench / 日志 / 波形 / 时序报告 / 参考模型 / 固件
```

系统只定义四类正式组件：

1. 用户任务型 Skill；
2. 专业 Subagent；
3. 项目级确定性工具；
4. 工程产物和项目记录。

---

# 5. OMP 主会话职责

OMP 主会话是唯一协调入口。

## 5.1 负责

- 理解用户目标；
- 匹配一个或多个 Skill；
- 按 Procedure 调用专业 Agent；
- 决定串行或并行执行；
- 读取上游 Agent 输出；
- 向下游 Agent传递必要上下文；
- 判断输入是否完整；
- 请求用户确认；
- 汇总最终结果；
- 决定正式文件写入位置；
- 按需调用 Project Steward。

## 5.2 不负责

OMP 主会话不应代替专业 Agent 完成：

- 大规模 RTL 结构分析；
- 完整 testbench 设计；
- 复杂 Bug 根因判断；
- 时序路径专项分析；
- RTL 与参考模型差异定位；
- 外设驱动实现；
- 长期项目事实维护。

简单且边界明确的任务可以直接完成。

需要独立专业责任或多阶段交接的任务应调用对应 Subagent。

## 5.3 不创建 Orchestrator Agent

项目中不创建：

```text
orchestrator.md
main-controller.md
workflow-runner.md
```

OMP 主会话已天然承担协调职责。

---

# 6. 用户任务型 Skills

首版定义九个用户任务型 Skill。

每个 Skill 直接对应一类用户目标，而不是内部微方法。

---

## 6.1 rtl-architecture-analysis

### 解决问题

- 梳理模块接口；
- 梳理实例层级；
- 梳理数据流；
- 梳理时钟和复位域；
- 识别状态机；
- 识别协议边界和潜在风险。

### 主要 Agent

```text
rtl-analyst
```

### 主要输出

```text
rtl-analysis.md
interface-table.md
module-hierarchy.md
dataflow.md
clock-reset-map.md
risk-notes.md
```

### Procedure 示例

1. 确认待分析 RTL、顶层模块和分析范围；
2. 调用 `rtl-analyst`；
3. 使用 RTL Python 工具提取模块、端口、参数和层级；
4. 扫描时钟、复位、状态机和协议边界；
5. 对工具结果进行语义解释；
6. 标记无法确定的动态行为；
7. 生成结构分析报告。

---

## 6.2 rtl-to-testbench

### 解决问题

- 根据现有 RTL 搭建 testbench；
- 生成 stimulus；
- 生成 scoreboard；
- 建立 self-checking 流程；
- 生成仿真脚本；
- 输出验证结果。

### 主要 Agent

```text
rtl-analyst
verification-engineer
simulation-analyst
```

### 主要输出

```text
verification-plan.md
tb/*.sv
vectors/*
run_sim.*
verification-report.md
```

### Procedure 示例

1. 确认 DUT 文件、顶层模块、输出目录和仿真器；
2. 调用 `rtl-analyst` 提取接口、时钟、复位和协议；
3. 校验接口分析是否完整；
4. 缺少关键行为定义时请求用户补充；
5. 调用 `verification-engineer` 设计验证计划；
6. 在隔离 worktree 中生成 testbench 和运行脚本；
7. 执行仿真；
8. 失败时调用 `simulation-analyst` 定位首个失败；
9. 输出 testbench、日志和验证报告；
10. 用户确认后再应用到正式工程。

---

## 6.3 spec-to-design

### 解决问题

- 根据接口说明撰写设计方案；
- 根据算法说明规划 RTL 架构；
- 拆分模块；
- 设计接口和数据格式；
- 分析吞吐、延迟、缓冲和带宽；
- 规划时钟域和验证方案。

### 主要 Agent

```text
design-architect
rtl-analyst
model-consistency-analyst
```

### 主要输出

```text
design-proposal.md
module-breakdown.md
interface-contract.md
dataflow.md
performance-budget.md
verification-strategy.md
risk-list.md
```

### Procedure 示例

1. 提取需求、接口、算法和性能约束；
2. 区分已确认要求与设计假设；
3. 调用 `design-architect` 生成初步架构；
4. 涉及现有系统时调用 `rtl-analyst` 核对接入边界；
5. 涉及数值算法时调用 `model-consistency-analyst` 检查数据格式；
6. 计算吞吐、延迟、缓存和带宽预算；
7. 输出模块拆分、接口契约、风险和验证策略；
8. 将关键假设显式提交用户确认。

---

## 6.4 bug-investigation

### 解决问题

- 定义 Bug 现象；
- 整理 Observation；
- 建立 Hypothesis；
- 管理支持证据和反证；
- 设计区分性实验；
- 记录已排除方向；
- 形成根因状态；
- 输出下一步行动。

### 主要 Agent

```text
debug-investigator
rtl-analyst
verification-engineer
simulation-analyst
model-consistency-analyst
firmware-engineer
```

根据问题范围按需选择，不要求全部调用。

### 主要输出

```text
investigation.md
observations.md
hypotheses.md
evidence-index.md
experiments.md
root-cause-status.md
next-actions.md
```

### Procedure 示例

1. 定义实际现象、期望行为和复现条件；
2. 调用 `debug-investigator` 建立调查框架；
3. 按问题类型调用 RTL、仿真、模型或固件 Agent；
4. 将观察、推断和结论分离；
5. 为每个假设记录支持证据和反证；
6. 设计能够区分多个假设的实验；
7. 执行实验并更新假设状态；
8. 输出已确认根因、剩余不确定性或下一实验；
9. 不因证据不足强行给出修复。

---

## 6.5 model-consistency

### 解决问题

- 对比 RTL 与 Python/C++/MATLAB 参考模型；
- 对齐输入输出；
- 处理定点数和符号位；
- 处理端序；
- 分析舍入、饱和和溢出；
- 定位首个 mismatch；
- 生成差异统计。

### 主要 Agent

```text
model-consistency-analyst
rtl-analyst
simulation-analyst
```

### 主要输出

```text
comparison-spec.md
normalization-config.json
comparison-report.md
mismatch.csv
first-mismatch.md
numeric-risk.md
```

### Procedure 示例

1. 冻结相同输入数据；
2. 定义 RTL 与参考模型的输入输出映射；
3. 明确位宽、符号、端序、舍入和饱和规则；
4. 分别运行 RTL 和参考模型；
5. 使用比较工具归一化输出；
6. 找到首个 mismatch；
7. 调用 `rtl-analyst` 反向追踪相关数据路径；
8. 区分模型错误、接口错误、数值误差和 RTL 错误；
9. 输出差异报告和复现配置。

---

## 6.6 simulation-analysis

### 解决问题

- 分析仿真日志；
- 分析 assertion failure；
- 分析波形；
- 定位首个异常周期；
- 分析时序报告；
- 聚合回归失败；
- 区分环境、工具、验证和设计问题。

### 主要 Agent

```text
simulation-analyst
rtl-analyst
verification-engineer
```

### 主要输出

```text
simulation-analysis.md
first-failure.json
signal-window.csv
timing-summary.md
failure-clusters.json
```

### Procedure 示例

1. 判断输入属于日志、波形、时序或回归结果；
2. 使用对应 Python Parser 提取结构化数据；
3. 定位第一个失败时间点或最差时序路径；
4. 识别相关信号、模块和时钟域；
5. 必要时调用 `rtl-analyst` 补充结构上下文；
6. 必要时调用 `verification-engineer` 判断测试环境问题；
7. 输出证据、判断和建议下一步；
8. 不将日志中的最后一个错误误认为首要根因。

---

## 6.7 regression-framework

### 解决问题

- 扫描现有测试；
- 设计回归目录和命名规则；
- 生成测试 runner；
- 统一测试结果格式；
- 聚合 PASS/FAIL；
- 输出失败摘要。

### 主要 Agent

```text
verification-engineer
simulation-analyst
```

### 主要输出

```text
regression-plan.md
regression.*
tests/*
results-schema.json
regression-report.md
```

### Procedure 示例

1. 扫描现有 testbench、脚本和测试数据；
2. 定义测试分类和命名约定；
3. 定义统一的命令行入口；
4. 定义 PASS、FAIL、SKIP 和 BLOCKED 结果；
5. 生成回归 runner；
6. 使用 fixture 验证结果聚合；
7. 调用 `simulation-analyst` 检查失败分类；
8. 输出可重复运行的框架和使用说明。

---

## 6.8 firmware-development

### 解决问题

- 调试软核 C 程序；
- 核对寄存器表；
- 开发外设驱动；
- 分析中断、DMA 和启动流程；
- 分析 linker 和编译问题；
- 调试 UART、SPI、I²C、QSPI 等接口；
- 核对软硬件契约。

### 主要 Agent

```text
firmware-engineer
rtl-analyst
debug-investigator
```

### 主要输出

```text
firmware-analysis.md
register-map-check.md
driver-design.md
driver/*
debug-plan.md
firmware-test-plan.md
```

### Procedure 示例

1. 收集 C 代码、寄存器说明、RTL 接口和构建信息；
2. 调用 `firmware-engineer` 分析软件流程；
3. 调用 `rtl-analyst` 核对寄存器和握手语义；
4. 检查访问宽度、地址、字节序、中断和 DMA；
5. 形成驱动设计或修复方案；
6. 在不访问真实设备的条件下完成静态和构建验证；
7. 需要板级操作时先请求用户确认；
8. 输出驱动、调试计划和剩余硬件依赖。

---

## 6.9 project-steward

### 解决问题

- 维护项目状态；
- 维护待办；
- 维护已验证结论；
- 维护设计决策；
- 维护调查索引；
- 清理过期结论。

### 主要 Agent

```text
project-steward
```

### 主要输出

```text
.project/status.md
.project/tasks.md
.project/verified-facts.md
.project/decisions.md
.project/risks.md
.project/investigations/
```

### Procedure 示例

1. 读取最近完成的正式工程产物；
2. 提取已验证事实、决策、风险和待办；
3. 检查事实是否有明确证据；
4. 检查旧结论是否已失效或被替代；
5. 生成拟更新内容；
6. 请求用户确认；
7. 更新 `.project/`；
8. 不记录普通聊天和未经验证推断。

---

# 7. Skill 标准结构

每个 Skill 遵循：

```text
.omp/skills/<skill-name>/
├── SKILL.md
├── references/
└── templates/
```

只有 `SKILL.md` 是 OMP 发现入口。

`references/` 和 `templates/` 由该 Skill 按需读取，不注册为顶层 Skill。

## 7.1 SKILL.md 必需章节

```markdown
---
name: <skill-name>
description: <明确说明触发场景>
---

# Skill Title

## When to use

## Do not use

## Required inputs

## Optional inputs

## Procedure

## Delegation

## Tools

## Outputs

## Validation

## Failure handling

## Safety
```

## 7.2 Procedure 的定位

Procedure 是对 OMP 主会话的执行指导。

Skill 本身不会主动调用 `task`、`bash` 或其他 Tool。

Procedure 应明确：

- 需要哪些输入；
- 调用哪些 Agent；
- 串行还是并行；
- 调用哪些工具；
- 何时请求用户确认；
- 正式产物写到哪里；
- 出错后如何处理。

第 6 章只提供简要 Procedure 示例。

各 Skill 的完整执行规格应写入对应 `SKILL.md`，避免顶层设计与实现长期重复。

---

# 8. 专业 Subagents

Agent 配置位于：

```text
.omp/agents/
```

## 8.1 rtl-analyst

负责：

- RTL 结构；
- 接口；
- 层级；
- 数据流；
- 时钟和复位；
- FSM；
- 协议边界；
- RTL 风险。

默认只读，不修改 RTL。

## 8.2 design-architect

负责：

- 需求到架构；
- 算法到模块；
- 接口契约；
- 性能预算；
- 缓冲和存储；
- 风险；
- 验证策略。

默认不生成正式实现代码。

## 8.3 verification-engineer

负责：

- 验证计划；
- stimulus；
- scoreboard；
- assertion；
- testbench；
- 回归；
- 验证结果。

允许在隔离目录生成验证代码。

默认不修改 DUT。

## 8.4 simulation-analyst

负责：

- 仿真日志；
- assertion；
- 波形；
- 首个失败；
- 时序报告；
- 回归失败聚类。

默认只读。

## 8.5 debug-investigator

负责：

- 问题定界；
- Observation；
- Hypothesis；
- Evidence；
- 反证；
- 区分性实验；
- 根因状态。

默认不修改代码。

## 8.6 model-consistency-analyst

负责：

- 参考模型映射；
- 定点数；
- 符号；
- 端序；
- 舍入；
- 饱和；
- mismatch；
- 差异统计。

不默认认定参考模型正确。

## 8.7 firmware-engineer

负责：

- 软核 C；
- 寄存器访问；
- 外设驱动；
- 中断；
- DMA；
- 启动；
- linker；
- 固件日志；
- 软硬件接口。

未经确认不访问真实设备。

## 8.8 project-steward

负责：

- 项目状态；
- 待办；
- 已验证事实；
- 决策；
- 风险；
- 调查索引。

只能整理已有工程结论，不创造技术结论。

---

# 9. Agent 调用和协作

## 9.1 默认协作方式

首版采用：

```text
OMP 主会话
→ task 调用 Agent A
→ 主会话读取 Agent A 输出
→ task 调用 Agent B
→ 主会话汇总
```

Agent 之间不默认直接通信。

## 9.2 Agent 输出引用

Agent 输出引用用于：

- 当前任务的临时交接；
- 主会话读取子 Agent 结果；
- 下游 Agent 消费上游摘要；
- 避免复制大量文本。

Agent 输出引用不作为：

- 长期项目事实源；
- 正式设计文档；
- testbench；
- 调查报告；
- 版本控制产物。

## 9.3 正式产物

以下内容必须写入文件系统：

- testbench；
- 仿真脚本；
- 设计方案；
- 调查报告；
- 差异报告；
- 回归框架；
- 固件驱动；
- 项目状态；
- 已验证结论。

## 9.4 并行调用

互不依赖的任务可以并行：

```text
接口分析
时钟域分析
状态机分析
```

有明确数据依赖的任务必须串行：

```text
接口分析
→ testbench 设计
→ 仿真
→ 失败分析
```

## 9.5 Hub

首版不使用 Hub 作为默认协作机制。

原因：

- OMP 主会话已能处理串行调度；
- OMP task 已能处理并行任务；
- Agent 输出引用已能满足临时交接；
- 正式工程产物应进入文件系统；
- Hub 会引入额外协作状态和失败边界；
- 首版尚无明确案例证明必须使用 Hub。

只有真实案例证明以下场景无法通过主会话串行、并行或批处理解决时，才考虑 Hub：

- 多个长时间运行 Agent 必须在运行期间持续相互触发；
- 主会话成为明显的性能或逻辑瓶颈；
- Agent 需要在任务完成前动态请求其他 Agent 追加调查。

Hub 不用于：

- 普通串行 Agent 交接；
- 独立并行分析；
- 长期工程事实保存；
- 正式产物传递；
- 替代 `.project/` 或文件系统。

---

# 10. 确定性工具

首版工具统一优先使用 Python。

工具位于：

```text
tools/
```

工具首先是可独立运行的 Python CLI，不要求注册为 OMP Custom Tool。

## 10.1 RTL 工具

```text
tools/rtl/
├── extract_modules.py
├── extract_interfaces.py
├── build_hierarchy.py
├── scan_clock_reset.py
└── scan_fsm.py
```

## 10.2 仿真工具

```text
tools/simulation/
├── run.py
├── parse_log.py
├── extract_failures.py
└── aggregate_regression.py
```

## 10.3 波形工具

```text
tools/waveform/
├── list_signals.py
├── extract_window.py
└── export_csv.py
```

## 10.4 时序工具

```text
tools/timing/
├── parse_paths.py
├── group_violations.py
└── summarize.py
```

## 10.5 模型比较工具

```text
tools/model_compare/
├── normalize_data.py
├── compare.py
├── fixed_point.py
├── endianness.py
└── first_mismatch.py
```

## 10.6 固件工具

```text
tools/firmware/
├── parse_map.py
├── check_register_access.py
└── parse_log.py
```

## 10.7 工作区辅助工具

首版优先使用 OMP task 原生隔离能力。

只补充必要脚本：

```text
tools/workspace/
├── capture_baseline.py
├── verify_clean.py
└── summarize_diff.py
```

不开发新的 worktree 管理器。

## 10.8 OMP Custom Tool 注册

首版不强制将 Python CLI 注册为 OMP Custom Tool。

大部分首版工具通过 `bash` 调用即可。

以下情况可考虑注册为 Custom Tool：

- 调用频率高，需要更稳定的接口；
- 参数复杂，需要 Schema 校验；
- 输出需要被其他 Agent 或 Tool 稳定解析；
- 路径和参数组合复杂，bash 容易调用错误；
- 需要结构化返回结果；
- 需要工具级风险控制；
- 需要更合适的交互呈现。

工具注册是可选升级，不是每个 Python CLI 的必经阶段。

主会话在调用高风险工具前，可以使用 OMP 确认机制请求用户决定。

该确认流程与 Custom Tool 本身的参数校验和风险控制应分别设计，不视为同一机制。

---

# 11. 工程产物与项目记录

## 11.1 临时输出

以下信息可以仅存在于当前 OMP 会话：

- Agent 分析草稿；
- 临时摘要；
- 中间推断；
- 当前阶段交接信息；
- 可重新生成的结果。

## 11.2 正式工程产物

正式产物写入用户项目的合理位置，例如：

```text
verification/
tb/
scripts/
docs/design/
docs/investigations/
reports/
firmware/
```

写入位置按以下优先级确定：

1. 用户指定位置；
2. 项目已有约定；
3. Skill 推荐默认路径。

## 11.3 长期项目记录

统一使用：

```text
.project/
├── status.md
├── tasks.md
├── verified-facts.md
├── decisions.md
├── risks.md
└── investigations/
```

`.project/` 是人和 Agent 都可阅读的轻量工程记录，不是 Runtime 数据库。

## 11.4 写入条件

只有以下情况才更新 `.project/`：

- 用户明确要求；
- 一个任务阶段完成；
- 一个结论被实际验证；
- 一个设计决策被确认；
- 一个阻塞被建立或解除；
- 一个调查形成长期价值。

不自动记录：

- 普通聊天；
- 未验证推断；
- 每次 Tool 调用；
- 全量日志；
- 可随时重新生成的中间内容。

---

# 12. 上下文策略

每次 Agent 调用只传递必要上下文。

## 12.1 MUST_HAVE

- 任务目标；
- 相关文件；
- 顶层模块；
- 当前代码版本；
- 输入输出定义；
- 当前现象；
- 预期产物；
- 写入边界。

## 12.2 USEFUL

- 旧调查；
- 相似模块；
- 相关设计文档；
- 旧日志；
- 现有测试；
- 参考模型。

## 12.3 EXCLUDED

默认不传递：

- 完整聊天历史；
- 全部工程目录；
- 无关构建产物；
- 无来源旧结论；
- 已过期日志；
- 大量重复波形；
- 与当前任务无关的项目记录。

---

# 13. 安全模型

## 13.1 默认只读

分析、调查和评审 Agent 默认只允许：

```text
READ
SAFE_EXECUTE
```

## 13.2 修改前确认

任何正式修改前，主会话必须展示：

```text
拟修改文件
修改目的
影响范围
验证方法
回滚方法
```

获得用户确认后才能进入正式写入。

不建设 Approval 对象。

## 13.3 隔离执行

生成或修改代码时，优先使用 OMP task 原生隔离。

首版默认采用稳定、可检查的 worktree 模式。

标准流程：

```text
创建临时 worktree
→ 生成或修改文件
→ 执行验证
→ 展示 diff 和验证结果
→ 用户确认
→ 应用 patch、复制产物或由用户决定合并
```

示例：

- 生成 testbench 时在临时 worktree 中写入；
- 原工作区保持不变；
- 仿真通过后展示新增文件和日志；
- 不默认自动 merge 回当前分支。

## 13.4 默认禁止

- 自动 commit；
- 自动 push；
- 自动 merge；
- 自动删除用户工程文件；
- 自动烧写板卡；
- 自动升级固件；
- 自动重置设备；
- 自动清理用户工作区。

---

# 14. 失败处理

系统不建立通用状态机，但所有 Skill 必须遵循统一失败分类：

```text
INPUT_MISSING
TOOL_UNAVAILABLE
TOOL_FAILED
AGENT_FAILED
OUTPUT_INVALID
VALIDATION_FAILED
WORKSPACE_CONFLICT
```

## 14.1 输入缺失

- 明确指出缺失内容；
- 请求用户补充；
- 不猜测关键接口语义。

## 14.2 Tool 不可用

- 报告缺失命令或环境；
- 给出安装或替代方式；
- 不声称验证完成。

## 14.3 Agent 失败

- 主会话读取失败信息；
- 允许最多一次有针对性的重试；
- 重试仍失败则报告阻塞；
- 不由主会话伪造 Agent 结果。

## 14.4 输出不完整

- 不进入下一阶段；
- 指明缺失字段或产物；
- 要求 Agent 重做或请求用户补充。

## 14.5 验证失败

- 保留失败证据；
- 不自动修改 DUT；
- 不隐藏失败；
- 必要时转入 `bug-investigation`。

## 14.6 工作区冲突

- 停止写入；
- 展示冲突文件；
- 由用户决定使用当前工作区、隔离副本或新分支。

---

# 15. 项目目录结构

```text
develoip-copilot/
├── .omp/
│   ├── skills/
│   │   ├── rtl-architecture-analysis/
│   │   │   ├── SKILL.md
│   │   │   ├── references/
│   │   │   └── templates/
│   │   ├── rtl-to-testbench/
│   │   │   ├── SKILL.md
│   │   │   ├── references/
│   │   │   └── templates/
│   │   ├── spec-to-design/
│   │   ├── bug-investigation/
│   │   ├── model-consistency/
│   │   ├── simulation-analysis/
│   │   ├── regression-framework/
│   │   ├── firmware-development/
│   │   └── project-steward/
│   └── agents/
│       ├── rtl-analyst.md
│       ├── design-architect.md
│       ├── verification-engineer.md
│       ├── simulation-analyst.md
│       ├── debug-investigator.md
│       ├── model-consistency-analyst.md
│       ├── firmware-engineer.md
│       └── project-steward.md
├── tools/
│   ├── rtl/
│   ├── simulation/
│   ├── waveform/
│   ├── timing/
│   ├── model_compare/
│   ├── firmware/
│   └── workspace/
├── fixtures/
│   ├── rtl/
│   ├── simulation/
│   ├── timing/
│   ├── waveform/
│   ├── model_compare/
│   └── firmware/
├── evals/
├── docs/
└── README.md
```

不建立：

```text
workflows/
runtime/
events/
adapters/
task-database/
```

---

# 16. 与其他 OMP Skills 的集成

## 16.1 集成原则

- 不复制已有通用能力；
- 不覆盖现有 Skill；
- 不依赖未声明的外部 Skill；
- 外部 Skill 作为可选增强；
- 核心流程在没有外部 Skill 时仍可工作。

## 16.2 可复用能力

可能复用：

- 通用代码评审；
- Git 操作；
- TDD；
- 文档生成；
- 项目交接；
- 环境诊断；
- 工具安装。

## 16.3 冲突处理

多个 Skill 同时可能触发时：

- 优先选择最接近用户最终产物的 Skill；
- 其他 Skill 作为内部辅助；
- 不要求用户手动组合多个底层方法。

例如：

```text
根据 RTL 搭建 testbench
```

应触发：

```text
rtl-to-testbench
```

而不是要求用户分别调用：

```text
接口提取
testbench 规划
仿真运行
日志分析
```

---

# 17. 实施路线

## Milestone 1：OMP 原生骨架

### 实现范围

首批 Agent：

```text
rtl-analyst
verification-engineer
simulation-analyst
```

首批 Skill：

```text
rtl-architecture-analysis
rtl-to-testbench
simulation-analysis
```

同时建立：

- Skill 标准模板；
- Agent 标准模板；
- fixture 约定；
- eval 约定；
- Python CLI 规范；
- OMP 发现和调用 smoke test。

### 验收标准

文件存在性：

```text
.omp/skills/ 下存在预期 Skill
.omp/agents/ 下存在预期 Agent
tools/ 下 Python CLI 可直接运行
```

OMP 真实性验证：

- OMP 能发现三个 Skill；
- OMP 能通过 `task` 解析并调用三个 Agent；
- Skill 内 references 可以成功读取；
- Skill Procedure 能串联两个 Agent；
- Agent 输出能被主会话继续消费；
- Python Tool 能被 Skill 流程调用；
- 一次 Agent 失败能被明确报告；
- 一次不完整输入能被正确阻断。

不以 `ls` 结果代替 OMP 发现验证。

---

## Milestone 2：RTL 理解

### 实现范围

- RTL 模块、端口和参数提取；
- 模块层级；
- 时钟和复位扫描；
- RTL 架构分析 Skill。

### Fixtures

- 简单组合逻辑模块；
- 带参数和状态机的时序模块；
- 一个已知语法错误模块；
- 一个缺少顶层信息的输入。

### 验收标准

- 正确提取接口；
- 正确识别层级；
- 正确识别主要时钟和复位；
- 正确报告语法错误；
- 缺少顶层时不盲目猜测；
- 生成可读 RTL 分析报告。

---

## Milestone 3：Testbench 生成

### 实现范围

- testbench 规划；
- stimulus；
- scoreboard；
- 仿真运行；
- 日志解析；
- `rtl-to-testbench` Skill。

### Fixture 验收

- 对简单 DUT 生成可运行 self-checking testbench；
- 能识别故意注入的 DUT 错误；
- 仿真工具不可用时正确报告阻塞。

### 真实工程验收

- 对一个边界清晰的真实模块生成可用验证框架；
- 不要求首轮支持复杂系统级 DUT；
- 记录无法自动推断的接口行为。

---

## Milestone 4：日志、波形和时序

实现：

- 仿真日志分析；
- 首个失败定位；
- 波形窗口提取；
- 时序报告解析。

验收：

- 已知错误日志；
- 已知异常波形；
- 已知负 slack 时序报告；
- 一个真实项目报告。

---

## Milestone 5：Bug 调查

实现：

- Debug Investigator；
- `bug-investigation` Skill；
- Observation、Hypothesis 和 Evidence 模板；
- 区分性实验方法。

验收：

- 一个已知根因案例；
- 一个真实未解决案例；
- 一个无法闭合但成功缩小不确定性的案例。

---

## Milestone 6：模型一致性

实现：

- 数据归一化；
- 定点数；
- 端序；
- 首个 mismatch；
- 差异统计。

验收：

- 已知一致样例；
- 已知端序错误；
- 已知定点舍入差异；
- 一个真实 RTL 与 Python/C++ 模型案例。

---

## Milestone 7：后续能力

按实际价值分别推进：

```text
spec-to-design
project-steward
firmware-development
regression-framework
```

不要求四者在同一 Milestone 一次完成。

---

# 18. 验证策略

## 18.1 每个 Skill 独立验证

每个 Skill 至少包含四类样例。

### 1. 正常 Fixture

特征：

- 输入完整；
- 格式正确；
- 预期输出明确；
- 场景规模较小；
- 结果可自动或人工精确校验。

用途：

- 验证基本流程；
- 验证 Tool；
- 验证 Agent 调用；
- 验证输出结构。

### 2. 错误 Fixture

特征：

- 输入中包含已知错误；
- 错误类型和预期行为已知。

示例：

- RTL 语法错误；
- testbench 故意失败；
- 时序报告存在负 slack；
- 参考模型端序错误；
- 定点精度不一致；
- 仿真日志包含 assertion failure。

用途：

- 验证 Skill 能识别问题；
- 验证不会伪造成功结果；
- 验证失败处理路径。

### 3. 不完整输入

特征：

- 缺少关键文件、字段或语义。

示例：

- 未指定顶层模块；
- 缺少时钟周期；
- 缺少接口行为说明；
- 缺少参考模型输入格式；
- 缺少仿真器。

用途：

- 验证 Skill 能指出缺失项；
- 验证不会盲目猜测；
- 验证用户补充流程。

### 4. 真实工程样例

特征：

- 来自实际项目；
- 规模和复杂度高于 Fixture；
- 可能包含不完整文档和历史包袱；
- 不一定有唯一标准答案。

用途：

- 验证真实实用性；
- 验证鲁棒性；
- 发现 Fixture 无法覆盖的问题；
- 评估相对普通 OMP 的价值。

真实工程样例首版不要求全部成功，但必须记录：

- 成功部分；
- 失败部分；
- 人工介入；
- 工具缺口；
- Skill 缺口；
- 后续改进方向。

## 18.2 对比基线

关键任务比较：

```text
普通 OMP 主会话
vs
develoip-copilot Skill + 专业 Agent
```

## 18.3 评价指标

- 正确性；
- 完整性；
- 工程产物可执行性；
- 人工补充次数；
- 错误修改次数；
- 上下文重复输入量；
- 执行时间；
- Token 成本；
- 最终产物复用价值。

## 18.4 停止条件

某个能力在多个真实案例中无法体现相对普通 OMP 的价值时：

- 暂停扩展；
- 判断问题位于 Skill、Agent、Tool 还是模型；
- 不通过增加更多流程层掩盖专业能力不足；
- 必要时删除或合并该能力。

---

# 19. 成功标准

首版成功不以 Skill、Agent 或测试数量衡量。

成功标准：

1. OMP 能正确发现 Skill 和 Agent；
2. Skill 能正确匹配用户任务；
3. Skill 能选择适当的专业 Agent；
4. Agent 交接不依赖完整聊天历史；
5. RTL 分析结果准确可用；
6. 能生成可运行 testbench；
7. 能分析真实日志、波形或时序报告；
8. 能形成可信 Bug 调查过程；
9. 能定位 RTL 与参考模型首个差异；
10. 正式修改前会请求用户确认；
11. 不会默认修改用户当前工作区；
12. 正式工程产物可以进入用户项目；
13. 长期项目记录简洁且有证据；
14. 相比普通 OMP 对话具有明确工程价值。

---

# 20. 最终设计决议

`develoip-copilot` v2.1 采用：

```text
OMP 主会话
+ 九个用户任务型 Skills
+ 八个专业 Subagents
+ Python 确定性工具
+ OMP 原生 task 调度
+ Agent 输出引用用于临时交接
+ 文件系统保存正式工程产物
+ .project 保存长期项目记录
```

明确不建设：

```text
独立主控 Agent
独立 Workflow 层
通用 Runtime
Event Store
Gate Engine
Approval 或 Acceptance 对象
统一任务产物数据库
默认 Hub 协作
自定义工作区隔离框架
```

开发顺序必须遵循：

```text
真实用户任务
→ 用户任务型 Skill
→ 专业 Agent
→ 确定性 Tool
→ 可执行工程产物
→ Fixture 验证
→ 真实案例验证
```

而不是：

```text
先建设通用平台
→ 再寻找 FPGA 使用场景
```

首个正式实施目标为：

> 使用 OMP 原生 Skill、三个专业 Agent 和 Python Tool，完成一个 Fixture RTL 模块的结构分析，并在其基础上生成可运行的自检 testbench；随后使用一个真实、边界清晰的 RTL 模块验证该流程的工程价值。
