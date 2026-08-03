# rtl-change-impact-review

目的：在明确 WRITE Approval 和 Baseline 下检查 RTL fixture 修改范围、接口影响和风险升级。

输入：授权 Scope、Approval、Baseline、RTL Artifact 候选和影响说明。

输出候选：RTL Artifact、Risk Proposal、影响分析和待验证条件。

硬边界：没有当前 WRITE Approval 不注册正式 RTL 修改；不能静默删除新增 Risk；不能由 RTL Engineer 关闭高风险问题。

权威规则：[execution-contract.md](../docs/execution-contract.md) 第 7、8 节。
