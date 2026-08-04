# 仿真分析报告 — <case_name>

> 本模板由 `simulation-analysis` skill 的 `simulation-analyst` 填充。
> 字段固定，未确定的内容写入「不确定性」段，禁止用猜测填补证据缺口。

## 元信息

| 项 | 值 |
| --- | --- |
| 案例名称 | <case_name> |
| 输入类型 | 日志 / 波形 / 时序报告 / 回归结果 |
| 输入文件 | <path> |
| 分析时间 | <YYYY-MM-DD HH:MM> |
| 关联 DUT / TB | <module> / <tb> |
| 分析者 | simulation-analyst（+ rtl-analyst / verification-engineer 按需） |

## 摘要

<2–4 句结论：首个失败是否已定位、根因大致归类、下一步建议。>

## 证据

### 结构化提取结果

| 工具 | 输入 | 关键输出（摘要） |
| --- | --- | --- |
| parse_log.py | <log> | errors=<n> warnings=<n> test_result=<PASS/FAIL> |
| extract_failures.py | <log> | 首个失败 time=<t> type=<error/warning> |
| aggregate_regression.py | <dir/*.log> | total=<n> passed=<n> failed=<n> |

> 波形（`signal-window.csv`）与时序（`timing-summary.md`）为 **Milestone 4 待实现能力**，工具未落地时不产出，见 artifacts-schema.md 标注。

### 首个失败详情

| 字段 | 值 |
| --- | --- |
| 时间点 | <t> |
| 信号 / 路径 | <sig> |
| 消息 | <message> |
| 关联模块 / 时钟域 | <module> / <clock_domain> |
| 证据来源 | <tool + file:line> |

## 判断

### 问题分类

| 类别 | 是否 | 置信度 | 依据 |
| --- | --- | --- | --- |
| 环境（编译/仿真器/路径） | 是/否 | 高/中/低 | <依据> |
| 工具（仿真器 bug/版本） | 是/否 | 高/中/低 | <依据> |
| 验证（TB/激励/参考模型） | 是/否 | 高/中/低 | <依据> |
| 设计（DUT 逻辑） | 是/否 | 高/中/低 | <依据> |

> 置信度规则见 references/failure-classification.md。分类结论须来自工具证据，不得仅凭末行错误判断。

### 失败聚类（多失败场景）

| 聚类 ID | 关联失败 | 共同特征 | 可能根因 |
| --- | --- | --- | --- |
| C1 | <list> | <feature> | <hypothesis> |

## 建议下一步

1. <具体动作 + 负责方（设计/验证/环境）>
2. <若需交叉引用，调用 rtl-analyst 补充结构上下文 / verification-engineer 判断测试环境>

## 不确定性

- <未确定的动态行为、工具未覆盖的信号、需编译器验证的项>
- <本案例未使用的能力（如波形/时序）及其原因>
