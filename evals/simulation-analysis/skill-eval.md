# Skill Eval — simulation-analysis

> 对齐 design §6.6 与 §1684「能分析真实日志、波形或时序报告」。
> 本 eval 为 Agent/Skill 端到端评估，结果表由真实执行填写（TODO）。
> 波形/时序类（Case C）因 Milestone 4 工具未实现，预期行为为「诚实报告待实现」。

## 评估方式

- 输入：仿真日志 / 波形 / 时序报告 / 回归结果目录
- 过程：skill 调用 `simulation-analyst` + 工具链，按 `templates/simulation-analysis.md` 产出
- 判分：每项按 rubric 计 pass/partial/fail

## Case A — 简单日志：定位首个失败并解释

- **输入**：`fixtures/simulation/error/sim_fail.log`（含 assertion failure at 120ns）
- **预期**：
  - 使用 `extract_failures.py --first-only` 定位首个失败 time=120
  - 不把日志末行错误当首要根因
  - 报告含证据/判断/建议/不确定性四段（模板字段齐全）
- **Rubric**：
  - pass：首个失败时间点正确 + 四类分类 + 建议下一步 + 不确定项列出
  - partial：定位正确但缺分类或建议
  - fail：定位错误 / 把末错当根因 / 伪造证据

## Case B — 失败日志：区分环境与设计问题

- **输入**：`fixtures/simulation/error/sim_fail.log`（error_count=3，含 width mismatch 警告）
- **预期**：
  - 区分「设计问题（assertion 触发于 DUT 数据比对）」与「环境/验证（width mismatch 警告）」
  - 对每类给出置信度（参考 `references/failure-classification.md`）
- **Rubric**：
  - pass：分类正确 + 置信度合理 + 低置信度写入不确定性段
  - partial：分类方向对但置信度缺失
  - fail：误将环境警告当设计根因 / 反之

## Case C — 波形/时序输入：正确报告工具待实现

- **输入**：一个波形文件（.vcd/.wlf）或时序报告（.rpt）（当前 fixtures 暂无，属 Milestone 4 待补）
- **预期**：
  - skill 识别输入类型，调用 `tools/waveform/extract_window.py` 或 `tools/timing/parse_paths.py`
  - 发现工具未实现，**诚实报告 Milestone 4 待办**，**不伪造** `signal-window.csv` / `timing-summary.md`
- **Rubric**：
  - pass：明确报告工具未实现 + 建议待落地后重试
  - fail：伪造波形/时序产物 / 静默跳过

## 回归聚合（附加）

- **输入**：`fixtures/simulation/normal/sim_pass.log` + `fixtures/simulation/error/sim_fail.log`
- **预期**：`aggregate_regression.py` 返回 total=2 passed=1 failed=1
- 由 `smoke_test.py::check_regression_aggregation` 自动化断言

## 结果表（TODO — 真实执行后填写）

| Case | 执行日期 | 结果 | 备注 |
| --- | --- | --- | --- |
| A 简单日志 | | | |
| B 环境/设计区分 | | | |
| C 波形/时序待实现 | | | |
| 回归聚合 | | | 自动化：smoke_test PASS |
