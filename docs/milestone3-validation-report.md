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

## 4.1 Gate A 正式判定（2026-08-03）

| # | Gate A 项 | 判定 | 证据 |
| --- | --- | --- | --- |
| 1 | OMP 可发现项目 Skill | **PASS** | `.omp/skills/develoip-copilot/SKILL.md`；交互会话 doctor skill 检查 PASS |
| 2 | OMP 可加载 Extension | **PASS** | 真实会话工厂执行；`session_start` 自动拉起 Bridge（12 次 ready） |
| 3 | `/dc doctor` 通过 | **PASS** | 交互会话 RESULT: PASS（11 项检查，约 2s） |
| 4 | OMP 可启动 Python Bridge | **PASS** | 真实会话 + pytest subprocess 全套 |
| 5 | `dc_query` 可读取 Runtime | **PASS** | 模型真实调用 dc_query 并渲染状态 |
| 6 | `dc_dispatch` 可创建 Task | **PASS** | `/dc m3-start` 建 task-m3；模型 CLASSIFY+BIND_BASELINE 成功 |
| 7 | `/dc resume` 可恢复 Event Store | **PASS（Bridge 层）** | pytest：重启 replay 恢复 + restore op + 陈旧快照降级；`/dc resume` 交互演示并入 Batch 2 M3-O11 |
| 8 | OMP Session 不保存第二套状态 | **PASS（设计审查）** | Extension 仅持 Bridge 连接；无 Session 历史导入路径 |
| 9 | Derived Result 写入被拒绝 | **PASS** | SET_GATE_STATUS → DERIVED_RESULT_WRITE_FORBIDDEN（pytest + smoke） |
| 10 | 未授权 edit/write/bash 被拦截 | **PASS** | 真实会话 M3-O03：模型 write 被拦截、文件未创建；决策矩阵 pytest 全覆盖 |
| 11 | Bridge 崩溃后可恢复 | **PASS** | smoke：stop→restart→replay 恢复；pytest：进程重启 |
| 12 | Milestone 2 Adapter tests 保持通过 | **PASS** | pytest 74 passed（含 M2 41 项） |

**结论：Gate A = PASS（12/12）**。判定依据：`docs/milestone3-validation-report.md` §2 自动化证据 + §3.1 真实交互会话证据；2026-08-03 复核，全量回归 74 passed、smoke PASS、`git diff --check` PASS。Batch 1 已提交为 `a70ca90`（完成Milestone3-Batch 1）。

## 5. 剩余限制与待用户确认项

1. **Gate A 已在真实交互会话闭环**（§3.1：doctor PASS、m3-start、dc_query/dc_dispatch 模型调用、
   M3-O03 越权写拦截）。用户新窗口中若遇到 `/dc doctor` 卡住，是修复前版本或 Extension 未重新加载
   的旧会话；请重启 OMP 会话后重试。`/dc resume` 跨会话恢复演示（M3-O11）在 Batch 2 引入真实
   Baseline 后正式执行。
2. 当前 `.omp/dc-state/` 内存在验证过程产生的 events.jsonl / snapshot.json / bridge.stderr.log
   （gitignored，不计入提交），其中 `task-m3` 为交互验证期间创建的真实 M3 顶层 Task
   （PROPOSED→READY，scope=probe-dir，baseline=baseline-a）；正式试点从 Batch 2 重新对齐。
3. 本报告未声称：真实硬件验证、生产工程修改、板级问题关闭。

---

# Batch 2 — 真实 Workspace 与 Baseline（2026-08-03）

## 自动化验证

```text
python -m pytest -q   → 99 passed（M2 41 + Batch 1 33 + workspace 25）
python -m compileall -q runtime roles tools adapters fixtures tests workspace → PASS
bun tests/omp/smoke.ts → SMOKE PASS
git diff --check       → PASS
```

workspace 新增 25 项：scope 规则、adapter 快照/五态分类矩阵、baseline 确定性、
isolation（worktree/clone 原工作区零触碰 + patch 生成 + 清理）、bridge 集成
（workspace_status/capture_baseline/guard 分类拦截）。

## 真实试点验证（Bridge 直连，只读）

| 验证项 | 结果 |
| --- | --- |
| workspace_status | pilot_connected=true，classification=**CLEAN**，branch=feature_axi，commit=fb2ed49，0 脏文件 |
| 相关文件哈希 | MEM.TXT/qspi_driver_tb.v 等与手工捕获一致 |
| capture_baseline | 指纹 `fb2ed49a…:b097d3bd92e5875e`，4 文件哈希 + 工具链 + 输入引用，CLEAN |
| 基线验证（隔离镜像） | qspi_driver_tb **TEST PASSED，errors=0**（ReadStatus/Enter4Byte/ReadID/SingleRead/QuadRead/Erase/Program） |
| Guard（真实试点） | 治理范围内 write → **BLOCKED APPROVAL_REQUIRED**；范围外 write → ALLOWED；治理 cwd 内 bash 写意图 → BLOCKED |
| 原工作区 | 全程未被修改（基线验证在 `%TEMP%/dc-pilot-sim` 镜像中运行） |

## Gate B 判定

| # | Gate B 项 | 判定 | 证据 |
| --- | --- | --- | --- |
| 1 | 原工作区不被修改 | **PASS** | isolation 测试（worktree/clone 后原树不变）；仿真镜像运行 |
| 2 | 未提交修改不丢失 | **PASS** | adapter 只读快照 + 分类（DIRTY_RELATED/UNRELATED 测试） |
| 3 | Baseline 可重复捕获 | **PASS** | 确定性测试 + 真实捕获 |
| 4 | Scope 外修改被拒绝 | **PASS**（approval-scope 匹配 Batch 5 细化） | Guard 治理/分类拦截；`WORKSPACE_CONFLICTING` 测试 |
| 5 | protected path 不可写 | **PASS** | Guard PROTECTED_PATH（config.protected_paths 已接线） |
| 6 | 用户相关脏修改被识别 | **PASS** | 分类矩阵测试（五态全覆盖） |
| 7 | 工具执行副作用可审计 | **PASS** | baseline 记录工具链+输入引用；diff_before_after；镜像日志 |
| 8 | 不执行真实设备操作 | **PASS** | 全程无设备访问；仿真在隔离镜像 |
| 9 | Milestone 2 tests 保持通过 | **PASS** | pytest 99 passed（含 M2 41） |

**Gate B = PASS（9/9）**。待 Batch 5 前定义 `candidate_write_scope` 并细化 approval-scope 精确匹配。

---

# Batch 3 — OMP 专业角色集成（2026-08-03）

## 实现

- `.omp/agents/dc-*.md` 六个角色代理（name/description/tools allowlist/角色纪律 systemPrompt/输出协议）。
- 子代理一律不含 `dc_dispatch`；状态变更只经主控 `dc_submit_candidates` → `dc_dispatch`。

## 真实子代理链路（Gate C 最小调用）

| 角色 | 子代理 | 时长 | 产出 | 验证点 |
| --- | --- | --- | --- | --- |
| System Investigator | 真实 OMP 子代理 | 7m43s | 5 证据 + 6 声明 + 3 风险 + handoff | 静态交叉核对；被 dc-guard 拒绝创建隔离副本（WRITE 缺失）——Guard 生效实证 |
| Verification Engineer | 真实 OMP 子代理 | 5m58s | 2 工件 + 2 复现证据(E1) + 1 INFERENCE + 4 风险 | `%TEMP%/dc-verify-qspi` 隔离复现 TEST PASSED errors=0；复跑前后试点 CLEAN、哈希不变 |
| Integration Reviewer | 真实 OMP 子代理 | 2m38s | 1 评审工件 + 5 声明 → CONDITIONAL_ACCEPT | sim.log 物理核实、哈希复算、独立性/基线一致性；RECORD_ACCEPTANCE 入账 |

Runtime 状态（task-qspi-invest，baseline-qspi-a）：evidence=9、claims=7、artifacts=2、handoffs=1、
acceptance=CONDITIONALLY_ACCEPTED；gates：simulation=SATISFIED、integration=SATISFIED、
root_cause/implementation/record=UNSATISFIED（调查任务正常态）。

## 候选校验拦截实证（Gate C #8）

- `risk_type` ≠ 契约 `risk_factor` → CANDIDATE_INVALID（BRIDGE_INTERNAL_ERROR 已改为契约错误码）。
- `claim_type: verification_result` 不在 {FACT,OBSERVATION,INFERENCE,DECISION,HYPOTHESIS} → INVALID_ENUM。
- `integration-reviewer` REGISTER_ARTIFACT/CREATE_CLAIM → OWNERSHIP_VIOLATION（Reviewer 状态表达=Acceptance）。

## 修复的两个真实缺陷

1. Guard bash 目标感知（verification-engineer 报告）：`cp <治理路径> %TEMP%` 误判为治理写入 →
   `_bash_write_targets` + `_bash_governed` 目标感知判定；`tests/bridge/` 新增回归（含 cp 拷出放行、重定向/cp 写入作用域拦截）。
2. RECORD_ACCEPTANCE 大小写缺陷（D2）：`target["object_type"]="Claim"` vs 允许集 `"CLAIM"` → `.upper()` 归一化 + 回归测试。

## Gate C 判定

| # | Gate C 项 | 判定 | 证据 |
| --- | --- | --- | --- |
| 1 | ≥3 角色由真实 OMP 子代理执行 | **PASS** | investigator / verification-engineer / integration-reviewer 真实子代理（上表） |
| 2 | Role Invocation 不再使用测试 Stub | **PASS** | 链路全部真实子代理；候选经 dc_submit_candidates |
| 3 | Tool Allowlist 有效 | **PASS** | 角色 frontmatter tools；Investigator 无写工具 |
| 4 | Investigator 无 WRITE | **PASS** | allowlist 无写工具；其隔离副本创建被 dc-guard 拒绝（WRITE 缺失） |
| 5 | Engineer 无 Acceptance 权限 | **PASS** | ROLE_RULES：verification-engineer 无 RECORD_ACCEPTANCE/ACCEPT_HANDOFF |
| 6 | Reviewer 无实现权限 | **PASS** | reviewer REGISTER_ARTIFACT → OWNERSHIP_VIOLATION；allowlist 只读 |
| 7 | Documenter 无状态迁移权限 | **PASS（定义级）** | ROLE_RULES：documenter 仅 RECORD_DECISION；Batch 6 实跑 |
| 8 | 非结构化结果不自动激活 | **PASS** | CANDIDATE_INVALID / INVALID_ENUM / OWNERSHIP_VIOLATION 三次拦截实证 |
| 9 | 子代理失败形成正确 Blocker | **PASS（定义级）** | blocker_proposals → CREATE_BLOCKER（角色均允许）；本批无失败场景 |
| 10 | OMP task 隔离结果可回收和审查 | **PASS** | `%TEMP%/dc-verify-qspi` 目录/日志/波形留档；Reviewer 物理核实 |

**Gate C = PASS（10/10）**。
