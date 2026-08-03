# develoip-copilot Milestone 1 实施计划

> 文档用途：Milestone 1 的可执行、可验收、可追踪实施基线
> 目标：建立 OMP 原生骨架，证明 Skill/Agent/Tool 集成可行
> 完成标志：三个最小 Skill 可被发现、三个最小 Agent 可被调用、最小 Python CLI 可独立运行
> 明确不实现：完整 FPGA 专业能力（RTL 解析、testbench 生成、日志分析等分别移至后续 Milestone）

---

## Milestone 1 定位

### 不是什么

Milestone 1 **不是**：

- 完整实现 RTL 分析能力（移至 Milestone 2）
- 完整实现 testbench 生成能力（移至 Milestone 3）
- 完整实现仿真日志分析能力（移至 Milestone 4）
- 任何 FPGA 专业的完整能力

### 是什么

Milestone 1 **是**：

- 创建三个最小 Skill 框架
- 创建三个最小 Agent 框架
- 创建一个最小 Python CLI 规范
- 验证 Skill 发现
- 验证 Agent 调用
- 验证 references 读取
- 验证串行交接
- 验证失败和不完整输入处理

---

## 实施范围

### 首批最小 Agent (3 个)

只有配置文件，不实现完整专业能力：

```text
rtl-analyst (最小配置)
verification-engineer (最小配置)
simulation-analyst (最小配置)
```

### 首批最小 Skill (3 个)

实现最小可执行 Procedure 和 Delegation，仅验证 OMP 编排：

- rtl-architecture-analysis（验证单 Agent）
- rtl-to-testbench（验证两个 Agent 串行交接 + hello CLI）
- simulation-analysis（验证单 Agent）

### 基础设施

- Skill 标准模板
- Agent 标准模板
- fixture 约定
- eval 约定
- Python CLI 规范
- 一个最小 Python CLI（hello world）
- OMP 发现与调用 smoke test

---

## 验收标准

### 文件存在性

```text
.omp/skills/ 下存在三个最小 SKILL.md
.omp/agents/ 下存在三个最小 Agent 配置
tools/ 下存在最小 Python CLI
```

### OMP 真实性验证

- [ ] OMP 能发现三个 Skill
- [ ] OMP 能通过 `task` 解析并调用三个 Agent
- [ ] Skill 内 references 可以成功读取
- [ ] Skill Procedure 能串联两个 Agent
- [ ] Agent 输出能被主会话继续消费
- [ ] Python Tool 能被 Skill 流程调用
- [ ] 一次 Agent 失败能被明确报告
- [ ] 一次不完整输入能被正确阻断

**不以 `ls` 结果代替 OMP 发现验证。**

---

## 实施顺序

### Batch 1: 目录和模板

**任务目标**：建立项目基础目录和标准模板

**对应设计章节**：design.md §15, §17 Milestone 1

**实现范围**：
- 创建目录结构
- 建立 SKILL.md 标准模板
- 建立 Agent 标准模板
- 建立 fixture/evals 约定

**明确不做**：
- 不实现任何专业逻辑
- 不创建任何自定义工作区框架

**允许修改文件**：
- 根目录结构
- `.omp/`
- `fixtures/README.md`
- `evals/README.md`
- `docs/`

**验收方法**：
- 目录结构符合约定
- 模板包含所有必需章节（design.md §7.1, §8）

**设计不变量检查**：
- [ ] 未创建主控 Agent
- [ ] 未引入独立 Workflow 层
- [ ] 未引入通用 Runtime 对象

---

### Batch 2: 三个最小 Skill 与 Agent

**任务目标**：创建三个最小 Skill 和三个最小 Agent 配置

**对应设计章节**：design.md §6, §8, §17 Milestone 1

**实现范围**：

**Agent** (仅配置，无专业实现)：
- `.omp/agents/rtl-analyst.md`
- `.omp/agents/verification-engineer.md`
- `.omp/agents/simulation-analyst.md`
- 每个包含：职责、默认工具、安全边界、输入输出约定

**Skill** (最小可执行 Procedure，不实现 FPGA 专业语义)：
- `.omp/skills/rtl-architecture-analysis/SKILL.md`
- `.omp/skills/rtl-to-testbench/SKILL.md`
- `.omp/skills/simulation-analysis/SKILL.md`
- 每个包含：必需章节、最小可执行 Procedure、最小 Delegation

**最小 Procedure 示例（验证 OMP 编排，不越界）**：

`rtl-architecture-analysis`（单 Agent）：
```text
1. 接收固定 smoke 输入
2. 调用 rtl-analyst
3. 读取结果
4. 汇总结构化输出
```

`simulation-analysis`（单 Agent）：
```text
1. 接收固定 smoke 输入
2. 调用 simulation-analyst
3. 读取结果
4. 汇总结构化输出
```

`rtl-to-testbench`（两个 Agent 串行 + hello CLI）：
```text
1. 接收固定 smoke 输入
2. 调用 rtl-analyst
3. 读取结果
4. 调用 verification-engineer
5. 调用 hello CLI
6. 汇总结构化输出
```

**明确不做**：
- 不实现任何专业分析逻辑
- 不实现 FPGA 专业语义
- 不实现任何 FPGA 工具

**允许修改文件**：
- `.omp/agents/*.md`
- `.omp/skills/*/SKILL.md`

**验收方法**：
- 配置符合模板标准
- OMP 能发现三个 Skill
- 最小 Procedure 可执行

**设计不变量检查**：
- [ ] Skill 对应用户任务
- [ ] Agent 配置位于 `.omp/agents/*.md`
- [ ] 未引入独立 Workflow 层

---

### Batch 3: 最小 Python CLI 规范和 hello CLI

**任务目标**：建立 Python CLI 规范和一个最小可运行示例

**对应设计章节**：design.md §10, §17 Milestone 1

**实现范围**：

**Python CLI 规范**：
- `tools/README.md`
- 定义 CLI 约定（参数、输出格式、错误码）
- 定义测试约定

**最小 hello CLI**：
- `tools/hello/hello_cli.py`
- 基本参数解析
- JSON 输出
- 错误处理

**明确不做**：
- 不实现任何专业工具
- 不注册 OMP Custom Tool

**允许修改文件**：
- `tools/README.md`
- `tools/hello/`

**验收方法**：
- hello CLI 可独立运行
- 输出符合规范
- pytest 通过

**设计不变量检查**：
- [ ] Python CLI 可脱离 OMP 独立运行
- [ ] 未注册 Custom Tool
- [ ] 未实现 FPGA 专业逻辑
- [ ] stdout/stderr 和错误码符合 CLI 规范

---

### Batch 4A: OMP 能力探针

**任务目标**：验证 OMP 是否提供可自动驱动的 CLI/API

**对应设计章节**：design.md §17 Milestone 1

**实现范围**：
- 验证是否存在可自动驱动的 CLI/API
- 记录实际命令、输出和限制
- 区分可自动化步骤和需人工验证步骤

**明确不做**：
- 不假设 OMP 提供稳定的机器可读 Skill 列表
- 不假设 pytest 通过 CLI 可以获得 task 工具
- 不假设可以从 Python 测试进程读取 agent://

**允许修改文件**：
- `tests/omp/probe.py`
- `docs/omp-capabilities.md`

**验收方法**：
- 探针测试通过
- OMP 能力文档准确

**设计不变量检查**：
- [ ] 使用 OMP 原生能力
- [ ] 未绕过 OMP 发现机制

---

### Batch 4B: Smoke 自动化

**任务目标**：基于 4A 的探针结果，实现可自动化的 smoke test

**对应设计章节**：design.md §17 Milestone 1

**实现范围**：
- 能自动化的步骤写入 pytest
- 不能自动化的步骤生成 live-smoke checklist
- 生成证据文件模板

**明确不做**：
- 不在验证接口未确认前冻结完整自动化
- 不假设所有步骤都能自动化

**允许修改文件**：
- `tests/omp/smoke_test.py`
- `tests/omp/live-smoke-checklist.md`
- `tests/omp/evidence-template.json`

**验收方法**：
- 能自动化的测试通过
- live-smoke checklist 完整
- 证据模板可用

**设计不变量检查**：
- [ ] 使用 OMP 原生能力
- [ ] 未绕过 OMP 发现机制

---

### Batch 5: 失败、不完整输入和临时交接

**任务目标**：验证失败处理和临时交接

**对应设计章节**：design.md §14, §9.2

**实现范围**：
- Agent 失败场景测试
- 不完整输入场景测试
- Agent 输出临时交接测试

**明确不做**：
- 不实现复杂的失败恢复逻辑

**允许修改文件**：
- `tests/omp/`

**验收方法**：
- Agent 失败能被明确报告
- 不完整输入能被正确阻断
- Agent 输出能被临时交接

**设计不变量检查**：
- [ ] Agent 输出仅用于临时交接
- [ ] 未将临时输出当作长期事实源

---

### Batch 6: 冻结 M1 结果并生成 M2 计划

**任务目标**：冻结 Milestone 1 结果，准备 Milestone 2

**对应设计章节**：design.md §17 Milestone 2

**实现范围**：
- 更新 `docs/traceability.md` M1 状态为 PASS
- 创建 `docs/milestone2-plan.md`（RTL 理解能力）
- 记录 M1 验收证据

**明确不做**：
- 不开始 Milestone 2 实现

**允许修改文件**：
- `docs/traceability.md`
- `docs/milestone2-plan.md`

**验收方法**：
- traceability M1 条目全部 PASS
- M2 计划符合 design.md §17

**设计不变量检查**：
- [ ] M1 未实现完整 FPGA 专业能力
- [ ] M1 只验证 OMP 骨架

---

## 统一任务模板

后续所有任务使用以下格式：

```text
任务目标：
[一句话描述]

对应设计章节：
design.md v2.1 §XX.X

实现范围：
- 具体实现项 1
- 具体实现项 2

明确不做：
- 不做 X
- 不做 Y

允许修改文件：
- 具体文件路径

预期产物：
- 产物 1
- 产物 2

验收方法：
- 验收方法 1
- 验收方法 2

设计不变量检查：
- [ ] 检查项 1
- [ ] 检查项 2
```

---

## Gate 检查

### Gate A: 设计一致性（每个 Batch 开始前）

- [ ] 任务是否来自 design.md v2.1
- [ ] 是否属于当前 Milestone
- [ ] 是否新增了未计划的架构层
- [ ] 是否可以使用 OMP 原生能力解决

### Gate B: 能力正确性（每个 Batch 实施后）

- [ ] 基础测试是否通过
- [ ] OMP 真实性验证是否通过
- [ ] 设计不变量检查是否通过

### Gate C: Milestone Closure（Milestone 1 完成后）

- [ ] OMP 骨架可行
- [ ] 保持轻量
- [ ] 可以进入 M2

**Gate 是 Milestone 文档中的人工验收检查点，不实现 Gate Engine，不增加运行时状态。**

---

## 明确排除的能力

以下能力明确不包含在 Milestone 1 中，分别移至后续 Milestone：

### Milestone 2: RTL 理解能力
- RTL 模块、端口和参数提取
- 模块层级分析
- 时钟和复位扫描
- rtl-architecture-analysis 完整实现

### Milestone 3: Testbench 生成能力
- testbench 规划和生成
- stimulus 和 scoreboard 生成
- 仿真运行和日志解析
- rtl-to-testbench 完整实现

### Milestone 4: 仿真分析能力
- 仿真日志分析
- 首个失败定位
- 波形窗口提取
- 时序报告解析
- simulation-analysis 完整实现

### 后续 Milestone
- Bug 调查
- 模型一致性
- 设计、项目记录与固件
- 回归测试框架

---

## 版本

- v2.2: 2026-08-03, 修复最小 Procedure 矛盾，补充 Batch 3 检查，明确三个 Skill 差异
- v2.1: 2026-08-03, 根据评审收缩范围，移出 Milestone 2-4 专业实现
- v1.0: 2026-08-03, 基于 design.md v2.1 冻结版本初始化