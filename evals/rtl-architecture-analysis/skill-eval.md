# Skill Eval: rtl-architecture-analysis

> 验证层：Skill Eval（端到端流程、路由、失败处理）
> 对齐：docs/evaluation-plan.md §C / design.md §1437-1451
> 使用方式：端到端场景测试；Agent 产物质量另由 Agent Eval 评估
> 引用 fixtures：`fixtures/rtl/{normal,error,incomplete}/`

## 评估链路

```text
用户任务
 → Skill 匹配 (rtl-architecture-analysis)
 → Procedure 执行 (规划 → 工具取证 → 语义解释 → 标未确定 → 按模板生成)
 → Agent 调用 (rtl-analyst)
 → 失败处理 (不完整/语法错误/缺顶层)
 → 产物生成 (6 个模板文件)
```

## Case 1 — Normal（正常分析）

- 用户任务：「分析 fixtures/rtl/normal/counter.v 的接口、层级、时钟复位」
- 预期必须包含：
  - 6 个产物文件（rtl-analysis / interface-table / module-hierarchy / dataflow / clock-reset-map / risk-notes）
  - 接口表含 clk、rst_n、count 的方向与位宽（count 为 `[WIDTH-1:0]`）
  - 时钟域标注 clk(pos) / 复位 rst_n(低有效、异步)，有工具扫描证据
  - 不确定行为显式标「未确定」
- 禁止出现：
  - 伪称语法正确（`"success"` / `valid` 之类）
  - 臆造 design 中不存在的端口或层级
- 评分 rubric：产物齐全 30% / 字段对齐模板 30% / 时钟复位证据 25% / 不确定性声明 15%

## Case 2 — Error / Incomplete（失败处理）

- 用户任务：「分析 fixtures/rtl/error/syntax_bad.v」与「fixtures/rtl/incomplete/truncated.v」
- 预期必须包含：
  - 调用 `extract_modules` 返回空 → 判定输入不完整
  - 主动请求用户补充（文件/顶层/完整模块头），**不继续猜测**
  - 提示语法错误需编译器 / 仿真器验证（工具不编译）
- 禁止出现：
  - 伪称语法正确或分析成功
  - 在错误 / 截断输入上臆造完整接口或层级
- 已知局限（诚实边界）：轻量工具为正则解析、不编译，无法自动识别语法错误；
  完整性以 `extract_modules` 返回空为信号。

## Case 3 — Multi-module without top（多模块无顶层）

- 用户任务：「分析 fixtures/rtl/incomplete/multi_no_top.v」
- 预期必须包含：
  - 列出全部 3 个模块（fifo_ctrl / arbiter / crc8）
  - 请求用户指定顶层，不臆造 root/top
- 禁止出现：
  - 凭空指定某模块为顶层
  - 在层级中伪造跨模块实例

## 结果记录（执行后填写）

| Case | 状态 | 备注 |
|------|------|------|
| 1 Normal | TODO | 待端到端执行 |
| 2 Error/Incomplete | TODO | 待端到端执行 |
| 3 Multi-no-top | TODO | 待端到端执行 |

## 工具层配合验证

- `tests/omp/test_rtl_tools.py`：覆盖 error/incomplete 的「不崩溃、不伪造成功、不臆造顶层」断言
- `tests/omp/smoke_test.py`：覆盖四个工具在 normal fixture 上的真实 JSON 输出断言
