# investigation-evidence-chain

目的：把调查 Observation、Hypothesis、Evidence 和 Claim 建立可追溯引用链。

输入：Task、当前 Baseline、MUST_HAVE Context、观察来源和复现结果。

输出候选：Artifact、Evidence、Claim、Evidence Conflict 或区分性实验建议。候选对象必须由 Runtime Command 正式注册。

硬边界：不直接写 Claim Status、Gate Status 或 Closure；不把 Hypothesis 改写成 FACT；不跳过 Baseline 和反证登记。

权威规则：[execution-contract.md](../docs/execution-contract.md) 第 9 节。
