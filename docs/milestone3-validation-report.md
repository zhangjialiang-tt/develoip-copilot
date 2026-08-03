# Milestone 3 — Validation Report（Batch 1 / Gate A）

> 里程碑：Milestone 3 — OMP-Native Real Project Pilot
> 阶段：Batch 1 — OMP Execution Harness（Gate A）
> 语义权威：`docs/execution-contract.md`
> 计划文件：`docs/develoip-copilot-Milestone3执行计划.md`
> 决策记录：`docs/milestone3-omp-decisions.md`
> 偏差记录：`docs/milestone3-contract-deviations.md`

## 1. 冻结输入

| 项目 | 值 |
| --- | --- |
| milestone3 起始 commit | `d2a9ad8a70851fab7402c08c51cbfb80e75218cc`（`base/develop`） |
| omp_version | `omp/17.2.5` |
| bun_version | `1.3.14` |
| python_version | `3.11.3` |
| pytest_version | `9.1.1` |
| operating_system | Windows 11 Pro（win32 10.0.26200, x64） |

## 2. 自动化验证结果

```text
python -m pytest -q                      → 73 passed
python -m compileall -q runtime roles tools adapters fixtures tests → PASS
bun tests/omp/smoke.ts                   → SMOKE PASS（12 项）
git diff --check                         → PASS
```

pytest 73 项 = M2 全量回归（41 项原契约/适配器测试，保持通过）+ M3 新增 32 项
（bridge 协议、guard 启发式、bridge 子进程 E2E、candidate 映射、快照契约守护）。

冒烟测试 12 项覆盖：Extension 工厂加载与注册（guard/tools/command/renderer）、TS BridgeClient ↔
真实 Python Bridge 的 hello/status/dispatch/guard_check/派生写拒绝/崩溃重启恢复。

## 3. 真实 OMP 会话证据（本次执行环境内可验证部分）

在 `-p`（非交互 print）模式多次启动全新 OMP 会话（cwd=仓库根目录），获得以下真实加载证据：

1. **Extension 原生发现生效**：`.omp/extensions/develoip-copilot/index.ts` 被自动发现并执行工厂。
2. **session_start 生命周期生效**：Extension 的 `session_start` 处理器自动拉起 Python Bridge，
   每次会话在 `.omp/dc-state/bridge.stderr.log` 留下 `dc-bridge ready ... last_sequence=0`（累计 12 次，含验证用会话）。
3. **session_shutdown 生效**：会话结束写入 `.omp/dc-state/snapshot.json`（294B）。
4. 发现机制经验证为项目级原生发现（`<cwd>/.omp/extensions`），嵌套子目录 `develoip-copilot/index.ts` 可发现；
   通过探针确认顶层 `.ts` 与嵌套目录均被原生 glob 匹配，加载失败会逐路径报告且不中断其他加载。

### 3.1 交互会话闭环验证（PTY 驱动真实交互 OMP 会话，DeepSeek V4 Flash）

| 验证项 | 结果 | 证据 |
| --- | --- | --- |
| `/dc doctor` | **PASS**（约 2s，无挂起） | 11 项检查全 PASS：extension/omp/python/bridge/event_store/custom_tools/skill/git/isolation/pilot_repository |
| `/dc m3-start` | **PASS** | CREATE_TASK 成功；goal 含 em-dash 非 ASCII 完整保留；Event sequence 1；`/dc status` 显示 `task-m3 [PROPOSED]` 及 next legal actions |
| 模型调用 `dc_query` | **PASS** | 模型成功调用 dc_query(summary=true) 并渲染 Runtime 状态（last_sequence/active_blockers/pending_approvals/next_legal_actions） |
| 模型调用 `dc_dispatch`（CLASSIFY_TASK + BIND_BASELINE） | **PASS** | task-m3 进入 READY、scope=probe-dir、baseline=baseline-a、required_capabilities=[WRITE] |
| M3-O03 越权写入拦截 | **PASS** | 模型 `write` probe-dir/blocked.txt 被 Guard 程序化拦截（"Blocked by the Runtime guard"）；磁盘确认文件未创建 |
| `ctx.ui.notify` 输出 | **PASS** | doctor/status/m3-start 报告均可见渲染 |

### 3.2 交互会话中定位并修复的真实缺陷

1. **嵌套 omp 派生阻塞**：doctor 原实现 `pi.exec("omp", ["--version"])` 在交互模式阻塞数十秒
   （TUI 卡 Working…）。已移除嵌套派生；版本用冻结常量 + `DC_OMP_VERSION` 覆盖。
2. **Windows GBK 代码页损坏 JSONL**：非 ASCII payload（em-dash）经 GBK `surrogateescape` 解码为
   孤立代理 → Bridge 报 `BRIDGE_INTERNAL_ERROR: surrogates not allowed`，事件未落盘。
   已修复（Python `reconfigure(encoding="utf-8")` + `PYTHONIOENCODING=utf-8`/`PYTHONUTF8=1`），
   新增 `test_non_ascii_payload_round_trips_utf8` 回归（含重启 replay 校验）。
3. **appendEntry+renderer 命令输出不可见**：实测 renderer 从未被调用；命令输出改用 `ctx.ui.notify`。
4. **工具注册视图**：`getActiveTools/getAllTools` 不枚举 extension 工具（77 内置），但模型可调用
   （dc_query 实测成功）；doctor 检查改为注册 + bridge 健康语义。

## 4. Gate A 门禁核对

| # | Gate A 项 | 结论 | 证据 |
| --- | --- | --- | --- |
| 1 | OMP 可发现项目 Skill | **PASS** | `.omp/skills/develoip-copilot/SKILL.md`；doctor 的 skill 检查在交互会话 PASS |
| 2 | OMP 可加载 Extension | **PASS（真实会话）** | 第 3 节证据：工厂执行、Bridge 自动拉起 |
| 3 | `/dc doctor` 通过 | **PASS（交互会话）** | §3.1：11 项检查全 PASS，约 2s |
| 4 | OMP 可启动 Python Bridge | **PASS（真实会话 + 测试）** | bridge.stderr.log 多次 ready；pytest subprocess 全部通过 |
| 5 | `dc_query` 可读 Runtime | **PASS（模型真实调用）** | §3.1：模型调用 dc_query 并渲染状态；pytest：query/status |
| 6 | `dc_dispatch` 可创建 Task | **PASS（模型真实调用 + 命令）** | §3.1：`/dc m3-start` 建 task、模型 CLASSIFY/BIND_BASELINE；smoke：CREATE_TASK |
| 7 | `/dc resume` 可恢复 Event Store | **PASS（Bridge 层）** | pytest：重启后 replay 恢复 + 显式 restore op + 陈旧快照降级 |
| 8 | OMP Session 不保存第二套状态 | **PASS（设计审查）** | Extension 仅持有 Bridge 连接；工具每次经 `dc_query`；无 Session 历史导入代码路径 |
| 9 | Derived Result 写入被拒绝 | **PASS** | pytest + smoke：SET_GATE_STATUS → DERIVED_RESULT_WRITE_FORBIDDEN |
| 10 | 未授权 edit/write/bash 被拦截 | **PASS（真实会话 M3-O03）** | §3.1：模型越权 write 被拦截、文件未创建；pytest：approval/revoke/blocker/protected/bash 全链路 |
| 11 | Bridge 崩溃后可恢复 | **PASS** | smoke：stop→restart→状态经 replay 恢复；pytest：进程重启 |
| 12 | Milestone 2 Adapter tests 保持通过 | **PASS** | pytest 74 passed（含 M2 41 项） |

## 5. 剩余限制与待用户确认项

1. **Gate A 已在真实交互会话闭环**（§3.1：doctor PASS、m3-start、dc_query/dc_dispatch 模型调用、
   M3-O03 越权写拦截）。用户新窗口中若遇到 `/dc doctor` 卡住，是修复前版本或 Extension 未重新加载
   的旧会话；请重启 OMP 会话后重试。`/dc resume` 跨会话恢复演示（M3-O11）在 Batch 2 引入真实
   Baseline 后正式执行。
2. 当前 `.omp/dc-state/` 内存在验证过程产生的 events.jsonl / snapshot.json / bridge.stderr.log
   （gitignored，不计入提交），其中 `task-m3` 为交互验证期间创建的真实 M3 顶层 Task
   （PROPOSED→READY，scope=probe-dir，baseline=baseline-a）；正式试点从 Batch 2 重新对齐。
3. 本报告未声称：真实硬件验证、生产工程修改、板级问题关闭。
