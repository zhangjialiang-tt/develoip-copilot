---
name: rtl-architecture-analysis
description: >
  梳理 RTL 模块接口、实例层级、数据流、时钟复位域、状态机和协议边界。
  当用户需要分析现有 RTL 结构、提取接口清单、梳理模块层级、识别时钟域时使用。
---

# RTL 架构分析

## When to use

- 需要梳理模块接口（端口、参数、方向、位宽）
- 需要梳理模块实例层级（父子关系）
- 需要梳理数据流和信号连接
- 需要识别时钟和复位域
- 需要识别状态机和协议边界
- 需要标记潜在 RTL 风险

## Do not use

- 生成 testbench（使用 `rtl-to-testbench`）
- 分析仿真日志（使用 `simulation-analysis`）
- 生成设计方案（使用 `spec-to-design`）
- 调查 Bug（使用 `bug-investigation`）

## Required inputs

- RTL 文件路径（一个或多个 .v/.sv 文件）
- 顶层模块名称

## Optional inputs

- 分析范围（指定子模块或特定关注点）
- 已知时钟信号名称
- 已知复位信号名称

## Procedure

1. 确认待分析 RTL 文件、顶层模块和分析范围（用户未指定顶层时主动询问，不猜测）。
2. 调用 `rtl-analyst` 规划分析重点与关注点。
3. 使用确定性工具收集证据（优先 `--json` 结构化输出）：
   - `tools/rtl/extract_modules.py --json` 提取模块列表
   - `tools/rtl/extract_interfaces.py --json` 提取端口和参数
   - `tools/rtl/build_hierarchy.py --json` 构建实例层级
   - `tools/rtl/scan_clock_reset.py --json` 扫描时钟和复位
4. 基于工具证据识别状态机与协议边界（`rtl-analyst` 语义解释；当前无专用工具，须显式标注置信度与依据）。
5. 对工具结果进行语义解释，串联接口、层级、时钟域与数据流。
6. 标记无法确定的动态行为（显式写"未确定"及原因）。
7. 按 `templates/` 模板生成 6 个结构分析产物文件。

## Delegation

- `rtl-analyst`: RTL 结构语义解释、状态机/协议边界识别、风险标记、按 `templates/` 模板生成报告

## Tools

- `tools/rtl/extract_modules.py` — 提取模块定义列表
- `tools/rtl/extract_interfaces.py` — 提取端口和参数
- `tools/rtl/build_hierarchy.py` — 构建实例层级树
- `tools/rtl/scan_clock_reset.py` — 扫描时钟和复位信号

## Outputs

所有产物默认写入 `.project/rtl-analysis/<top_module>/`，或由用户在请求中指定目录。报告严格按 `templates/` 下对应模板生成，保持章节与表格字段固定。

- `rtl-analysis.md` — 结构分析主报告（总览 + 分项索引）
- `interface-table.md` — 接口清单表（模块 / 参数 / 端口方向位宽）
- `module-hierarchy.md` — 模块实例层级树
- `dataflow.md` — 数据流与关键信号连接
- `clock-reset-map.md` — 时钟与复位域映射
- `risk-notes.md` — 风险与不确定性备注

## Validation

- 接口清单与实际 RTL 端口定义一致
- 层级树无循环依赖
- 时钟域标注有工具扫描证据支持
- 无法确定的行为已显式标记为"未确定"

## Failure handling

- 完整性以 `extract_modules` 结果为权威信号：若其返回空列表，或模块数与 `build_hierarchy`/`extract_interfaces` 明显不一致，判定输入不完整（截断 / 语法错误 / 缺少顶层），主动请求用户补充，不继续猜测。
- 语法错误：当前工具为正则解析、**不编译**，无法自动识别语法错误。当模块头无法闭合导致 `extract_modules` 返回空时，按"输入不完整"处理并提示用户用编译器 / 仿真器验证；报告中不得伪称语法正确。
- 缺少顶层模块：请求用户指定，不臆造顶层（多模块文件必须由用户或调用方选定顶层）。
- 工具不可用：报告缺失命令和安装方式。

## Safety

- 默认只读，不修改 RTL 文件
- 分析报告默认写入 `.project/rtl-analysis/<top_module>/`，或用户指定目录
