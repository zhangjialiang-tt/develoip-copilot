---
name: rtl-to-testbench
description: >
  根据现有 RTL 搭建自检 testbench，包括 stimulus、scoreboard、仿真脚本和验证报告。
  当用户需要为已有 RTL 模块生成完整验证环境时使用。
---

# RTL 到 Testbench

## When to use

- 为已有 RTL 模块生成 testbench
- 生成 stimulus 和 scoreboard
- 建立 self-checking 验证流程
- 生成仿真运行脚本
- 输出验证结果报告

## Do not use

- 仅分析 RTL 结构（使用 `rtl-architecture-analysis`）
- 仅分析仿真日志（使用 `simulation-analysis`）
- 调查设计 Bug（使用 `bug-investigation`）

## Required inputs

- DUT RTL 文件路径
- 顶层模块名称
- 输出目录（用户未指定时默认 `.project/tb/<top_module>/`）

## Optional inputs

- 仿真器命令（默认自动检测：优先 vsim，退回 iverilog；均不可用则报告阻塞）
- 时钟周期定义
- 复位时序
- 协议行为说明
- 已知测试向量

## Procedure

1. 确认 DUT 文件、顶层模块、输出目录和仿真器（未指定输出目录时用默认 `.project/tb/<top_module>/`）
2. 调用 `rtl-analyst` 提取接口、时钟、复位和协议：先用 `tools/rtl/extract_interfaces.py`、`tools/rtl/scan_clock_reset.py` 取证，再由 agent 整合；协议无专用工具，由 agent 基于工具证据与用户说明推断并标注置信度
3. 校验接口分析是否完整（接口、时钟、复位、协议假设均闭合或显式标注未确定项）
4. 缺少关键行为定义时请求用户补充
5. 调用 `verification-engineer` 设计验证计划（按 `templates/verification-plan.md`）
6. 在隔离 worktree/目录中生成 testbench 与运行脚本（按 `templates/tb-top.sv.tmpl`、`templates/run_sim.sh.tmpl`；向量见 `templates/vectors.md`）
7. 执行仿真（使用 `tools/simulation/run.py`）
8. 失败时调用 `simulation-analyst` 基于 `tools/simulation/extract_failures.py` 定位首个失败
9. 输出 testbench、日志和验证报告（按 `templates/verification-report.md`）
10. 用户确认后再应用到正式工程

## Delegation

- `rtl-analyst`: 接口/时钟/复位提取与协议推断（协议为 agent 基于工具证据+用户说明推断，标置信度）
- `verification-engineer`: 验证计划、testbench 设计、仿真脚本（按 `templates/` 生成）
- `simulation-analyst`: 仿真失败分析，使用 `tools/simulation/extract_failures.py`、`aggregate_regression.py`（按需）

## Tools

- `tools/rtl/extract_interfaces.py` — 提取端口和参数
- `tools/rtl/scan_clock_reset.py` — 扫描时钟复位
- `tools/simulation/run.py` — 执行仿真
- `tools/simulation/parse_log.py` — 解析仿真日志
- `tools/simulation/extract_failures.py` — 提取首个/全部失败（供 simulation-analyst）
- `tools/simulation/aggregate_regression.py` — 回归结果聚合

## Outputs

- `verification-plan.md` — 验证计划（模板：`templates/verification-plan.md`）
- `tb/*.sv` — testbench 文件（骨架：`templates/tb-top.sv.tmpl`）
- `vectors/*` — 测试向量（模板：`templates/vectors.md`）
- `run_sim.*` — 仿真运行脚本（骨架：`templates/run_sim.sh.tmpl`）
- `verification-report.md` — 验证报告（模板：`templates/verification-report.md`）

默认输出目录：`.project/tb/<top_module>/`（用户指定时以其为准）。

## Validation

- 仿真器可用：先检测 vsim/iverilog，缺省用可用者；均不可用则按 design Milestone3 验收"正确报告阻塞"，不伪造编译成功
- testbench 可编译（仿真器返回零错误）
- 至少一个测试场景 PASS
- self-checking 机制已启用
- 验证报告与仿真日志一致

## Failure handling

- 仿真失败：保留日志，调用 simulation-analyst 用 `extract_failures.py` 定位首个失败
- 接口不完整或协议未知：请求用户补充行为定义，不在无依据时臆测
- 仿真器不可用：报告缺失命令（vsim 或 iverilog）与安装方式，不声称已编译通过

## Safety

- 默认不修改 DUT RTL
- 在隔离目录/worktree 中生成验证代码
- 仿真通过后展示 diff，用户确认后再合并
