# Milestone 3 — OMP 决策记录（milestone3-omp-decisions）

> 状态：Batch 1 进行中
> 语义权威：`docs/execution-contract.md`
> 计划文件：`docs/develoip-copilot-Milestone3执行计划.md`

## 1. 冻结输入记录（计划 §5）

| 项目 | 值 |
| --- | --- |
| milestone3 起始 commit | `d2a9ad8a70851fab7402c08c51cbfb80e75218cc`（`base/develop`） |
| milestone2 冻结 commit | `157764b`（M2 功能冻结）；`d2a9ad8` 为仅含 `.gitignore`/缓存清理的收尾提交 |
| omp_version | `omp/17.2.5` |
| bun_version | `1.3.14` |
| python_version | `3.11.3` |
| pytest_version | `9.1.1` |
| git_version | `2.52.0.windows.1` |
| operating_system | Windows 11 Pro（win32 10.0.26200, x64） |

## 2. OMP 平台机制冻结（Batch 1 验证）

| 项目 | 决策 |
| --- | --- |
| extension_loading_method | 项目级原生发现：`<cwd>/.omp/extensions/develoip-copilot/index.ts`（default export 工厂；Bun 直接导入 `.ts`，`?mtime` 缓存破坏）。不使用 `additionalExtensionPaths`/linked plugin，保持单一加载路径（计划 §8.2 要求）。 |
| custom_tool_loading_method | Custom Tool 由 Extension 通过 `pi.registerTool()` 注册（计划 §8.2/§8.4 允许"注册或装配"）。不使用 `.omp/tools` 文件发现，避免工具与 Bridge 生命周期分裂在两套加载机制。 |
| skill_discovery_method | 原生 `.omp/skills/develoip-copilot/SKILL.md`（非递归一层发现；frontmatter `description` 为必需）。 |
| task_isolation_mode | 复用 OMP `task` 子代理隔离能力（worktree/overlay），Batch 3 冻结具体模式；Batch 1 不自行实现子进程 Agent 框架。 |
| tool_approval_policy | 双层：OMP 平台 Tool Approval（平台层确认）AND Runtime Approval（工程语义授权）。OMP 的"允许"不自动生成 Runtime Approval（计划 §2.4）。 |

> **Batch 1 实测冻结（2026-08-03）**：在 omp/17.2.5 上以 `-p` 模式启动全新会话验证——
> 项目级原生发现 `<cwd>/.omp/extensions` 生效，嵌套目录 `develoip-copilot/index.ts` 可被发现并执行；
> 工厂在加载期执行；`session_start` 自动拉起 Python Bridge、`session_shutdown` 写入快照
> （证据见 `docs/milestone3-validation-report.md` 第 3 节）。
>
> **交互会话实测发现（2026-08-03，PTY 驱动真实交互会话复现）**：
> 1. 嵌套 `pi.exec("omp", ["--version"])` 在交互模式阻塞数十秒（TUI 卡在 Working…）。
>    修复：doctor 不再派生嵌套 omp，版本取冻结常量 `OMP_VERSION_FROZEN`（可用 `DC_OMP_VERSION` 覆盖）。
> 2. Windows 区域代码页（本机 GBK/cp936）损坏非 ASCII 的 JSONL 帧：UTF-8 字节被 stdin
>    `surrogateescape` 解码为孤立代理 → `BRIDGE_INTERNAL_ERROR: 'utf-8' codec can't encode ... surrogates not allowed`。
>    修复（双保险）：Bridge `main()` 对 stdin/stdout/stderr `reconfigure(encoding="utf-8")`；
>    TS 侧 spawn 环境注入 `PYTHONIOENCODING=utf-8` 与 `PYTHONUTF8=1`。回归测试
>    `tests/bridge/test_bridge_subprocess.py::test_non_ascii_payload_round_trips_utf8` + smoke 非 ASCII goal。
> 3. 命令输出必须用 `ctx.ui.notify`：`pi.appendEntry` + `registerMessageRenderer` 在本版本
>    命令上下文不会被渲染（实测 renderer 从未被调用）。
> 4. `getActiveTools()/getAllTools()` 在命令上下文不枚举 extension 注册的工具（仅 77 个内置），
>    但模型实际可调用（实测 dc_query 被模型成功调用并返回 Runtime 状态）。doctor 的 custom_tools
>    检查据此改为"注册 + bridge 健康 + Gate A 调用证据"语义。
| hook 机制 | 不单独使用 legacy Hook 目录；Extension `pi.on("tool_call")` 即 Tool Guard 的程序化拦截点（fail-closed）。 |

## 3. Bridge 协议决策

- 入口：`python -m runtime.omp_bridge --stdio --state-dir .omp/dc-state`。
- 帧格式：newline-delimited JSON；request `{id, op, params}`；response `{id, ok, result|error}`。
- 默认超时 30s（guard_check 10s，health 5s）。
- Ops：`hello, health, status, dispatch, query, restore, save_snapshot, invoke_role_result, submit_candidates, guard_check, workspace_status, shutdown`。
  - 相对计划 §8.3 最小集，新增 `status / submit_candidates / guard_check` 三个只读/校验型 op；均为协议转换，不引入第二状态源。
- 启动语义：Bridge 启动时从 Event Store 全量 replay（Event Store 是恢复权威）；陈旧快照不阻塞启动。显式 `restore` op 会验证快照一致性；快照陈旧时降级为 replay 并回报 `snapshot: "STALE"`。M2 的 `Runtime.restore` 严格拒绝语义保留并有测试守护（`tests/test_persistence.py`）。
- 崩溃恢复：TS 客户端检测到进程退出后，将未决请求以 `BRIDGE_DOWN` 显式失败（不产生部分成功 Event）；下一次请求自动重启 Bridge 并 replay 恢复。
- stderr：Bridge 日志隔离写入 `.omp/dc-state/bridge.stderr.log`，不污染 stdout 协议流。

## 4. 状态与目录决策

- Runtime 状态目录：`.omp/dc-state/`（events.jsonl、snapshot.json、config.json、bridge.stderr.log），已加入 `.gitignore`。Event Store 为本机执行账本，不入库；冻结证据以报告 + commit 引用为准。
- 物理目录调整（计划 §20 允许 Batch 1 调整，职责边界不变）：
  - Extension 源码放 `.omp/extensions/develoip-copilot/`（而非 `omp-extension/develoip-copilot/`），以获得原生自动发现；模块划分保持 `index/bridge/commands/tools/guards/session/renderers`。
  - Workspace Adapter（`workspace/` 目录）推迟到 Batch 2。

## 5. Tool Guard 决策（Batch 1 语义）

- 守护对象：`edit`、`write`、`ast_edit`、`bash`。
- 治理范围：仅当存在非终态（非 CLOSED/CANCELLED）Task 且目标路径落在其 Scope paths 内时拦截；未治理路径放行。`config.json.protected_paths` 无条件拒写。
- bash 分类：正则启发式识别写副作用（`sed -i`、重定向、`rm/mv/cp`、`git checkout --`/`reset`/`clean`/`push`/`commit`、PowerShell 写 cmdlet 等）→ WRITE_LIKELY；其余视为 READ。启发式清单在 `runtime/omp_bridge.py:BASH_WRITE_PATTERNS`，有单元测试守护（`tests/bridge/test_guard_logic.py`）。
- 放行条件：治理范围内写入必须同时满足——无活动 Blocker、存在 GRANTED 且 Baseline 匹配的 WRITE Approval。否则返回 `APPROVAL_REQUIRED` / `APPROVAL_PENDING` / `BLOCKER_ACTIVE` / `PROTECTED_PATH`。
- Bridge 不可达时 fail-closed（拒绝并提示 `/dc doctor`）。

## 6. 角色调用决策（Batch 1 语义）

- `dc_invoke_role` 校验 Role Request 必备字段（来自 Bridge `hello` 元数据，契约保留在 Python 侧），返回"用 OMP `task` 执行子代理 → 结构化输出 → `dc_submit_candidates`"的指令。真实子代理调度在 Batch 3 冻结。
- `dc_submit_candidates`：RoleInvocationLayer 校验角色输出（字段过滤 + 禁止字段拒绝），再由 `runtime/candidates.py` 生成幂等候选 Command（内容哈希 command_id）；候选必须逐条经 `dc_dispatch` 才生效。
- 禁止角色输出字段按 M3 计划 §10 对齐扩展：在 M2 四个 Derived Result 字段之外增加 `approval_granted`、`task_closed`（`runtime/roles.py`；M2 测试仅断言错误码，未破坏）。

## 7. 命令决策

- 单一 `/dc` 命令 + 子命令：`doctor | m3-start | status | resume | approve | reject | revoke | pause | cancel | close`。
- `/dc pause`：M1.5 契约无暂停状态迁移，命令存在但回报不支持（偏差 D1）。
- `/dc approve|reject|revoke` 展示 capability/scope/risk/baseline/申请角色/task，经 UI confirm 后以 actor=`user` dispatch 对应 Command（幂等 command_id）。

## 8. 验证命令

```text
python -m pytest -q
python -m compileall -q runtime roles tools adapters fixtures tests
bun tests/omp/smoke.ts
git diff --check
```

真实 OMP 会话内验证（`/dc doctor`、工具可调用、Guard 拦截）需在加载本 Extension 的会话中执行，见 `docs/milestone3-validation-report.md`（Batch 1 收尾时产出）。
