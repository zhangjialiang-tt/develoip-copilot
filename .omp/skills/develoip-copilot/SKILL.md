---
name: develoip-copilot
description: >
  develoip-copilot Runtime 执行纪律。凡涉及受控工程任务（Task、Approval、Baseline、
  Evidence、Claim、Gate、角色调度、工作区写入）的正式动作，必须通过 dc_* Custom Tool
  进入 Python Runtime；禁止用会话记忆、Todo 或 Markdown 计划充当状态源。
  触发：/dc 命令、dc_dispatch、dc_query、角色调用、WRITE 审批、Baseline、Gate、恢复任务。
---

# develoip-copilot 执行纪律

## 何时使用

- 用户提到 develoip-copilot、`/dc`、Milestone Task、Approval、Baseline、Gate、角色（Investigator/Engineer/Reviewer/Documenter）。
- 需要调查、修改或验证外部试点 FPGA 工程。
- OMP 会话重启后需要恢复任务上下文。

## 绝对规则

1. **Runtime 是唯一状态权威。** Task/Approval/Gate/Claim 进度只能来自 `dc_query`；
   不得从聊天记录、Todo、Memory 或本文件推断执行状态。
2. **所有写动作走单一入口。** 正式状态变更必须通过 `dc_dispatch` 提交 Runtime Command；
   OMP 工具 Approval 不能替代 Runtime Approval，两者必须同时满足。
3. **角色输出只是 Proposal。** 专业子代理输出必须先经 `dc_submit_candidates` 校验，
   再逐条 `dc_dispatch`；角色不得返回 gate_status / claim_status / closure_status /
   project_status / approval_granted / task_closed 字段。
4. **WRITE 防护是程序化门禁。** 不要尝试用 `edit`/`write`/`ast_edit`/带写副作用的 `bash`
   触碰受治理 Scope；Tool Guard 会拦截。被拦截时走 `/dc approve` 流程，不要绕过。
5. **恢复只从 Event Store。** 会话重启后使用 `/dc resume` 或 `dc_restore`；
   禁止从对话历史重建状态。
6. **未验证硬件不得声称板级问题关闭。** 只做仿真/代码范围结论时明确保留 hardware gate。

## 标准动作

| 需求 | 做法 |
| --- | --- |
| 查看进度 | `dc_query` (summary=true) 或 `/dc status` |
| 环境自检 | `/dc doctor` |
| 创建里程碑任务 | `/dc m3-start` |
| 调用专业角色 | `dc_invoke_role` → OMP `task` 子代理 → `dc_submit_candidates` → 逐条 `dc_dispatch` |
| 请求/授予 WRITE | 角色或 orchestrator `REQUEST_APPROVAL` → 用户 `/dc approve` |
| 撤销授权 | `/dc revoke <approval-id>` |
| 恢复 | `/dc resume` |

## 何时停下来请求用户决策

- 需要 WRITE / EXTERNAL_DEVICE_ACCESS / DESTRUCTIVE_OPERATION 授权；
- Evidence Conflict 或无法复现；
- Scope 需要扩大；
- 验证失败后是否返工；
- 长期 Record 写入与否。

## 角色边界速查

- orchestrator：建任务、选角色、请求 Approval；不改 RTL、不自验。
- system-investigator：READ/SAFE_EXECUTE、Evidence/Hypothesis；不写代码、不自证 Claim。
- rtl-engineer：授权 Scope 内 WRITE、局部自测；不改原工作区、不扩 Scope、不自接受。
- verification-engineer：独立复现与反证；不改实现、不把测试通过当整体关闭。
- integration-reviewer：Acceptance/拒绝；不改 RTL、不代签 Waiver。
- documenter：Record 候选与引用校验；不创建结论、不改状态。
