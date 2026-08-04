---
name: simulation-analysis
description: >
  分析仿真日志、定位首个失败、提取波形窗口、解析时序报告、聚合回归失败。
  当用户需要分析仿真结果、定位设计问题、分析回归失败时使用。
---

# 仿真分析

## When to use

- 分析仿真日志中的错误和警告
- 定位首个 assertion failure
- 提取特定时间窗口的波形信号
- 解析时序报告（setup/hold slack）
- 聚合和分析回归测试失败
- 区分环境、工具、验证和设计问题

## Do not use

- 生成 testbench（使用 `rtl-to-testbench`）
- 仅分析 RTL 结构（使用 `rtl-architecture-analysis`）
- 调查复杂 Bug（使用 `bug-investigation`）

## Required inputs

- 仿真日志文件（.log）或时序报告（.timing / .rpt）

## Optional inputs

- RTL 文件路径（用于交叉引用）
- 波形文件路径（.wlf / .vcd / .fsdb）
- 特定关注信号列表
- 回归测试结果目录

## Procedure

1. 判断输入属于日志、波形、时序或回归结果
2. 使用对应 Python Parser 提取结构化数据（见 Tools；波形/时序为 Milestone 4 待实现）
3. 定位第一个失败时间点或最差时序路径
4. 识别相关信号、模块和时钟域
5. 调用 `simulation-analyst` 基于证据做判断（**先证据后结论**，不把日志最后一个错误误认为首要根因）
6. 必要时调用 `rtl-analyst` 补充结构上下文
7. 必要时调用 `verification-engineer` 判断测试环境问题
8. 按 `templates/simulation-analysis.md` 输出证据、判断和建议
9. 波形/时序输入但对应工具未实现时，明确报告 Milestone 4 待办，**不伪造** `signal-window.csv` / `timing-summary.md`
10. 产物写入默认目录 `.project/sim-analysis/<case>/`（或用户指定）

## Delegation

- `simulation-analyst`: 日志分析、失败聚类、证据解释
- `rtl-analyst`: RTL 结构上下文补充（按需）
- `verification-engineer`: 测试环境判断（按需）

## Tools

- `tools/simulation/parse_log.py` — 解析仿真日志（可用）
- `tools/simulation/extract_failures.py` — 提取失败信息（可用）
- `tools/simulation/aggregate_regression.py` — 聚合回归结果（可用）
- `tools/waveform/extract_window.py` — 提取波形窗口（⚠️ **Milestone 4 待实现**，尚未落地）
- `tools/timing/parse_paths.py` — 解析时序路径（⚠️ **Milestone 4 待实现**，尚未落地）

> 波形/时序工具是 design §10.3/§10.4 规划的 Milestone 4 能力，目前目录为空、未实现。
> 收到波形/时序输入时按 Procedure 第 9 步诚实报告，不伪造产物。

## Outputs

- `simulation-analysis.md` — 分析主报告
- `first-failure.json` — 首个失败详情
- `signal-window.csv` — 波形窗口数据
- `timing-summary.md` — 时序摘要
- `failure-clusters.json` — 失败聚类结果

## Validation

- 首个失败时间点与日志一致
- 波形窗口时间范围正确
- 时序报告解析结果与原始报告一致
- 不将日志最后一个错误误认为首要根因

## Failure handling

- 日志格式不支持：报告格式要求，不猜测
- 工具不可用：报告缺失命令和安装方式
- 无法定位失败：报告已分析内容和剩余不确定性

## Safety

- 默认只读，不修改 DUT 或 testbench
- 分析报告写入用户指定目录
