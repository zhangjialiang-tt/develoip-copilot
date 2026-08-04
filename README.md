# develoip-copilot

面向个人 FPGA/嵌入式工程师的 OMP 原生专业能力套件。

## 当前状态



## 核心原则

复用 OMP 原生编排能力，以用户任务型 Skill 为入口，以专业 Subagent 为执行单元，以确定性工具提供工程能力。

## 设计文档

### [design.md](docs/design.md) ⭐ 基线设计

**状态**: FROZEN / BASELINE v2.1

**说明**: 核心设计文档，已冻结。后续可调整文件名、字段和实现细节，但未经评审不得改变核心架构语义。

**核心内容**:
- 产品定位和非目标
- 总体架构
- 九个用户任务型 Skill
- 八个专业 Subagent
- 确定性工具设计
- 安全模型
- 失败处理
- 实施路线

### [design-constraints.md](docs/design-constraints.md) 🚦 设计约束

**说明**: 十条设计不变量检查表，所有开发、代码评审和架构决策的第一检查项。

**用途**:
- 开发前确认不违反设计不变量
- 代码评审时检查架构一致性
- 架构决策时评估影响

**十条核心不变量**:
1. 不创建主控 Agent
2. 顶层 Skill 对应用户任务
3. 多 Agent 流程写入 Skill Procedure
4. 专业角色实现为 `.omp/agents/*.md`
5. 确定性能力首选独立 Python CLI
6. Python CLI 不强制注册为 Custom Tool
7. Agent 输出引用只用于临时交接
8. 正式产物写入文件系统，长期状态写入 `.project/`
9. 首版不默认使用 Hub
10. 不重新引入 Runtime、Event Store、Gate、Approval 等通用平台能力

### [traceability.md](docs/traceability.md) 🔍 设计追踪

**说明**: 追踪设计要求到具体实现的映射关系。

**用途**:
- 实施前确认任务对应的设计要求
- 实施后更新实现位置和状态
- 代码评审时检查实现是否追溯

**核心原则**:
- 每行实现必须能对应至少一条设计要求或真实案例需求
- 每条设计要求必须追踪到具体的实现位置

### [evaluation-plan.md](docs/evaluation-plan.md) ✅ 评估计划

**说明**: 定义 Fixture 和真实样例，指导能力验收。

**核心原则**:
- **没有测试样例，不开始写分析工具**

**四类 Fixture**:
1. 正常 Fixture：验证基本流程
2. 错误 Fixture：验证问题识别
3. 不完整输入：验证阻断能力
4. 真实工程样例：验证实用性和鲁棒性

### [milestone1-plan.md](docs/milestone1-plan.md) 📋 Milestone 1 计划

**说明**: Milestone 1 的可执行、可验收、可追踪实施基线。

**目标**: 建立三个 Skill 和三个 Agent，验证 OMP 原生骨架。

**完成标志**:
- 三个 Skill 可被发现
- 三个 Agent 可被调用
- Python CLI 可独立运行

### [design-deviations.md](docs/design-deviations.md) ⚠️ 设计偏差

**说明**: 记录实现必须偏离 design.md v2.1 的情况。

**核心原则**:
- **禁止因为"实现方便"直接修改架构**

**允许偏差的理由**:
1. OMP 实际能力与设计假设不符
2. Fixture 证明当前结构无法工作
3. 真实工程案例证明职责边界错误
4. 当前 Tool 方案无法满足正确性或性能要求

## 项目结构

```text
develoip-copilot/
├── .omp/
│   ├── skills/           # 用户任务型 Skill
│   └── agents/           # 专业 Subagent 配置
├── tools/                # Python 确定性工具
├── fixtures/             # 测试样例
├── evals/                # 能力评估
├── docs/                 # 文档
│   ├── design.md
│   ├── design-constraints.md
│   ├── traceability.md
│   ├── evaluation-plan.md
│   ├── milestone1-plan.md
│   └── design-deviations.md
└── README.md
```

## 实施顺序

### Milestone 1: OMP 原生骨架

1. **验证 OMP 原生骨架**
   - 创建目录结构
   - 建立 Skill/Agent 模板
   - OMP smoke test

2. **完成 rtl-architecture-analysis**
   - RTL 基础工具
   - rtl-analyst Agent
   - rtl-architecture-analysis Skill

3. **完成 simulation-analysis**
   - 仿真日志工具
   - simulation-analyst Agent
   - simulation-analysis Skill

4. **完成 rtl-to-testbench**
   - testbench 生成工具
   - verification-engineer Agent
   - rtl-to-testbench Skill

### Milestone 2+: 按设计文档推进

详见 [design.md §17](docs/design.md#17-实施路线)

## 停止规则

出现以下任一情况，应暂停开发并回看 design.md v2.1:

- [ ] 开始新增通用对象、状态或事件
- [ ] 新增了与 OMP 主会话重复的协调层
- [ ] 为一个 Fixture 建设大量通用框架
- [ ] 工具还没在真实案例中使用，就准备注册大量 Custom Tool
- [ ] Agent 数量增长，但用户任务能力没有增加
- [ ] 测试数量增长，但没有可运行工程产物
- [ ] 一个 Milestone 同时开发三个以上用户能力
- [ ] 为未来可能需求提前设计扩展点

## 设计不变量快速检查

每次开发或评审时：

- [ ] 是否新增了主控 Agent？
- [ ] 是否新增了独立 Workflow 层？
- [ ] 是否引入了新的通用 Runtime 对象？
- [ ] 是否把内部方法错误注册成顶层 Skill？
- [ ] 是否将临时 Agent 输出当作长期事实源？
- [ ] 是否绕过了用户确认或工作区隔离？

详细检查表见 [design-constraints.md](docs/design-constraints.md)。

## 统一任务模板

所有实施任务使用以下格式：

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

## 当前状态

- 设计基线：design.md v2.1 (FROZEN)
- 实施阶段：准备开始 Milestone 1
- 偏差记录：无

---

## 版本

- v2.1: 2026-08-03, 冻结设计基线，建立实施文档体系