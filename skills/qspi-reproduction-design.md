# qspi-reproduction-design

目的：为 QSPI 拼接异常设计确定性、可复现、边界明确的复现输入和检查方法。

输入：QSPI Task、Baseline、总线观察、拼接范围和预期输出。

输出候选：复现 Artifact、E2/E3 Evidence、覆盖说明和冲突实验建议。

硬边界：不访问真实板卡；不以重复同一实现冒充独立方法；不直接满足 Simulation/Protocol Gate。

权威规则：[execution-contract.md](../docs/execution-contract.md) 第 8、9 节。
