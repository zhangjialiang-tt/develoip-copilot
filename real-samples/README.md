# Real-world Samples（真实工程样例）

> 存储位置约定（见 docs/evaluation-plan.md）：
> `fixtures/` 可提交、可重复、预期明确的小型样例；
> `real-samples/` 默认本地或脱敏后的真实案例；
> `evals/` case 定义、rubric 和结果。

真实工程样例首版不要求全部成功，但必须记录状态与差距。

## 样例清单

### axi_stream_proc

- 来源：图像处理流水线数据接收模块（已脱敏）
- 存储位置：real-samples/rtl/axi_stream_proc.v
- 复杂度：中等
- 已知问题：
  - 内部 `en_div` 为 clk/2 使能分频，不是真实时钟；工具可能启发式误判为生成时钟
  - 子模块 `sync_fifo` 与本模块同文件，跨文件回填不适用
- 当前状态：部分支持
- 差距记录：
  - 状态机（IDLE/RECV/PROC/SEND）无专用工具，依赖 `rtl-analyst` 人工识别并标置信度
  - 数据流（AXI-Stream 握手 + FIFO 缓存）需 agent 基于工具证据梳理
