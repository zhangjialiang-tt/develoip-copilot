# verification-evidence-assessment

目的：针对明确 Baseline 评估复现、仿真和独立检查结果的可复现性、相关性、覆盖和独立性。

输入：验证 Artifact、命令/输入/工具版本、Reference 结果、Risk Policy。

输出候选：Evidence、覆盖缺口、反证、Verification Failure Blocker。

硬边界：E3 不自动等于充分；验证失败不能被实现者自测覆盖；不能直接写 Claim、Gate 或 Closure 状态。

权威规则：[execution-contract.md](../docs/execution-contract.md) 第 8、9、12 节。
