# 产物字段契约（artifacts schema）

> 说明 `simulation-analysis` skill 各产物的字段约定与产出条件。
> 工具输出为结构化数据，本文件规定其字段，供 agent 校验与报告引用。

## first-failure.json

由 `tools/simulation/extract_failures.py --first-only --json` 生成。

```json
[
  {
    "time": "120",        // 失败时间（仿真时间字符串）
    "message": "Assertion failure at time 120ns",
    "type": "error"       // error | warning
  }
]
```

- 通过日志：空数组 `[]`
- 多失败：仅取首个（`--first-only`）；如需全量去掉该开关

## failure-clusters.json

由 `simulation-analyst` 基于 `extract_failures.py` 全量输出聚类后写入（非工具直出）。

```json
[
  {
    "cluster_id": "C1",
    "failures": ["<time/message>", "..."],
    "common_feature": "<特征>",
    "likely_root_cause": "<假设>",
    "confidence": "high"   // high | medium | low
  }
]
```

## signal-window.csv — ⚠️ 条件产物（Milestone 4 待实现）

依赖 `tools/waveform/extract_window.py`，该工具**尚未落地**。
工具就绪后预期字段：

```csv
time,signal_name,value
120.0,clk,1
120.5,rst_n,0
```

启用条件：输入为波形文件（.wlf/.vcd/.fsdb）且 `tools/waveform/extract_window.py` 可用。

## timing-summary.md — ⚠️ 条件产物（Milestone 4 待实现）

依赖 `tools/timing/parse_paths.py`，该工具**尚未落地**。
工具就绪后预期包含：最差时序路径、slack 值（setup/hold）、负 slack 路径清单。
启用条件：输入为时序报告（.timing/.rpt）且 `tools/timing/parse_paths.py` 可用。

## 诚实边界

- 上述波形/时序产物为 design Milestone 4 规划能力，当前工具未实现。
- skill 收到波形/时序输入时，**不得伪造** `signal-window.csv` / `timing-summary.md`；
  应报告"对应工具尚未实现（Milestone 4）"，并建议待工具落地后重试。
