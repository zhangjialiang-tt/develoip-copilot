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
- 输出目录

## Optional inputs

- 仿真器命令（默认 vsim）
- 时钟周期定义
- 复位时序
- 协议行为说明
- 已知测试向量

## Procedure

1. 确认 DUT 文件、顶层模块、输出目录和仿真器
2. 使用 `tools/rtl/extract_interfaces.py` 提取 DUT 接口
3. 使用 `tools/rtl/scan_clock_reset.py` 提取时钟和复位
4. 调用 `rtl-analyst` 校验接口分析是否完整
5. 缺少关键行为定义时请求用户补充
6. 调用 `verification-engineer` 设计验证计划和 testbench
7. 在隔离 worktree 中生成 testbench 和运行脚本
8. 使用 `tools/simulation/run.py` 执行仿真
9. 失败时调用 `simulation-analyst` 定位首个失败
10. 输出 testbench、日志和验证报告
11. 用户确认后再应用到正式工程

## Delegation

- `rtl-analyst`: 接口提取校验
- `verification-engineer`: 验证计划、testbench 设计、仿真脚本
- `simulation-analyst`: 仿真失败分析（按需）

## Tools

- `tools/rtl/extract_interfaces.py` — 提取端口和参数
- `tools/rtl/scan_clock_reset.py` — 扫描时钟复位
- `tools/simulation/run.py` — 执行仿真
- `tools/simulation/parse_log.py` — 解析仿真日志

## Outputs

- `verification-plan.md` — 验证计划
- `tb/*.sv` — testbench 文件
- `vectors/*` — 测试向量
- `run_sim.*` — 仿真运行脚本
- `verification-report.md` — 验证报告

## Validation

- testbench 可编译（仿真器返回零错误）
- 至少一个测试场景 PASS
- self-checking 机制已启用
- 验证报告与仿真日志一致

## Failure handling

- 仿真失败：保留日志，调用 simulation-analyst 分析
- 接口不完整：请求用户补充行为定义
- 仿真器不可用：报告缺失命令和安装方式

## Safety

- 默认不修改 DUT RTL
- 在隔离目录/worktree 中生成验证代码
- 仿真通过后展示 diff，用户确认后再合并
