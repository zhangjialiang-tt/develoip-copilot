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

1. 确认待分析 RTL 文件、顶层模块和分析范围
2. 使用 `tools/rtl/extract_modules.py` 提取模块列表
3. 使用 `tools/rtl/extract_interfaces.py` 提取端口和参数
4. 使用 `tools/rtl/build_hierarchy.py` 构建实例层级
5. 使用 `tools/rtl/scan_clock_reset.py` 扫描时钟和复位
6. 调用 `rtl-analyst` Agent 对工具结果进行语义解释
7. 标记无法确定的动态行为
8. 生成结构分析报告

## Delegation

- `rtl-analyst`: RTL 结构语义解释、风险识别、报告生成

## Tools

- `tools/rtl/extract_modules.py` — 提取模块定义列表
- `tools/rtl/extract_interfaces.py` — 提取端口和参数
- `tools/rtl/build_hierarchy.py` — 构建实例层级树
- `tools/rtl/scan_clock_reset.py` — 扫描时钟和复位信号

## Outputs

- `rtl-analysis.md` — 结构分析主报告
- `interface-table.md` — 接口清单表
- `module-hierarchy.md` — 模块层级文档
- `clock-reset-map.md` — 时钟复位映射
- `risk-notes.md` — 风险备注

## Validation

- 接口清单与实际 RTL 端口定义一致
- 层级树无循环依赖
- 时钟域标注有工具扫描证据支持
- 无法确定的行为已显式标记为"未确定"

## Failure handling

- RTL 语法错误：报告具体文件和行号，不继续分析
- 缺少顶层模块：请求用户指定，不猜测
- 工具不可用：报告缺失命令和安装方式

## Safety

- 默认只读，不修改 RTL 文件
- 分析报告写入用户指定目录或默认输出目录
