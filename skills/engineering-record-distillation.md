# engineering-record-distillation

目的：把高价值工程结论压缩为可引用的长期 Record，并处置 `record_gate`。

输入：已发生 Runtime Event、Task/Claim/Evidence 引用、用户记录决策和去重结果。

输出候选：Record、引用校验结果、写入/拒绝/无需记录决定。

硬边界：不复制完整 Event Store、聊天记录、普通命令日志或原始波形；不创造 Runtime 状态迁移；用户拒绝长期记录不改变技术事实。

权威规则：[execution-contract.md](../docs/execution-contract.md) 第 13 节。
