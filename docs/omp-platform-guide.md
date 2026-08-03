# OMP 平台开发规范（develop-copilot 基础设施）

> 目标读者：在本仓库基于 OMP 开发 develop-copilot 底层基础设施的人。
> 目的：把「官方规范」与「本项目已踩/将踩的坑」固化下来，避免返工。

## 0. 权威来源与标注约定

| 来源 | 位置 | 权威级别 |
| --- | --- | --- |
| 官方内置文档（122 篇，随二进制版本化） | `omp read "omp://<name>.md"`，索引 `omp read "omp://"` | 高 |
| 官方 TypeScript 源码 | `C:\Users\zhangjl\node_modules\@oh-my-pi\pi-coding-agent\src\` | **最高（实现即事实）** |
| 官方示例 | 同上包内 `examples/{extensions,hooks,custom-tools,sdk}/` | 中 |
| 官网 | <https://omp.sh>（`/docs/tools`、`/docs/sdk`、`/docs/providers`） | 中 |

本文标注：`[源码 path:line]` = 已亲自核对源码；`[文档 x.md]` = 官方文档明确写的；`[未验证]` = 需实测。
**冲突时一律以源码为准**——本文已发现多处官方文档之间自相矛盾（见 §4.1）。

平台事实（本机实测）：`omp/17.2.5`，Bun 运行时，包名 `@oh-my-pi/pi-coding-agent`，MIT。

---

## 1. 扩展加载与发现

### 1.1 原生自动发现规则 `[文档 extension-loading.md]`

项目根：`<cwd>/.omp/extensions`；用户根：`~/.omp/agent/extensions`（受 `--profile`、`PI_CODING_AGENT_DIR` 影响）。

三种入口形态，**均只扫一层，不递归**：

1. 直接文件 `*.ts` / `*.js`
2. 子目录 `*/index.ts` / `*/index.js`（**TS 优先于 JS**）
3. 子目录 `*/package.json` 且含 `omp.extensions`（或 legacy `pi.extensions`）声明入口

本项目 `.omp/extensions/develoip-copilot/index.ts` 命中形态 2，同级 `bridge.ts`/`tools.ts` 等**不会**被误当作独立扩展入口——这个布局是对的。

### 1.2 ⚠️ 陷阱：原生发现会应用 gitignore

`[文档 extension-loading.md]`：原生自动发现使用 native glob，**`gitignore: true`、`hidden: false`**；而「显式配置目录扫描」走 `readdir`，**不应用 gitignore**。

**后果**：一旦有人往 `.gitignore` 写了 `.omp/`（很常见的"别提交本地状态"直觉），整个扩展会静默消失，且不报错。

本仓库现状**安全**（已实测 `git check-ignore` 未命中扩展与 skill，仅忽略 `.omp/dc-state/`）。请把这条写进 code review checklist：**永远不要用 `.omp/` 或 `.omp/*` 这种宽泛忽略规则**。

### 1.3 加载顺序与去重

顺序：原生自动发现 → JS/TS hook 工厂 → 已安装插件入口 → 显式配置路径（`-e/--extension`，然后 settings `extensions`）。
去重按**绝对路径、first-wins**。同一模块既被自动发现又被显式配置时，只在自动发现阶段加载一次。

**推论**：本项目决策"只用项目级原生发现、不用 `additionalExtensionPaths`"是正确的——混用两条路径只会得到同一个实例，却让排障变复杂。

### 1.4 禁用与隔离

- `--no-extensions` 禁用发现（显式 `-e` 仍加载）。
- `disabledExtensions: ["extension-module:<derivedName>"]`，`derivedName` 由入口路径推导：`/x/bar/index.ts` → `bar`。
- **扩展不沙箱**：同进程、共享一个 EventBus 和 ExtensionRuntime。加载期单个路径失败被捕获为 `{path, error}`，不阻断其他扩展。

---

## 2. 工厂契约与生命周期

```ts
import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
export default function myExt(pi: ExtensionAPI): void | Promise<void> {
  // 只允许注册，不允许运行时动作
}
```

生命周期 `[文档 extensions.md]`：
`导入模块 + 执行工厂（仅注册）` → `ExtensionRunner.initialize()` 接线运行时动作 → 开始派发事件。

### 2.1 ⚠️ 加载期禁止运行时动作

加载期调用 `pi.sendMessage()` 等动作方法会抛 `ExtensionRuntimeNotInitializedError` `[文档 extensions.md / loader.ts]`。
工厂里只做 `setLabel` / `on` / `registerTool` / `registerCommand`；**副作用（起子进程、连网络、读大文件）一律推迟到 `session_start` 或首次调用**。

本项目 `index.ts` 在工厂里 `new BridgeClient(...)` 是合规的——因为构造函数只拼路径、不启进程。**保持这个不变量**，不要在构造函数里 `ensureStarted()`。

### 2.2 ⚠️ 后台定时器必须用托管版本

`[文档 extensions.md]` 明确警告：扩展在主进程内无隔离。裸 `setInterval` / `setTimeout` / 游离 Promise 的回调若抛错，**逃出 handler 的 try/catch，被全局 postmortem 判定为 fatal，整个会话被拆毁**。

必须用 `ctx.setInterval` / `ctx.setTimeout` / `ctx.clearTimer`：错误被收敛到扩展错误通道、自动 `unref`、`session_shutdown` 时自动清理。

---

## 3. 事件系统

### 3.1 Handler 签名与调度

```ts
type ExtensionHandler<E, R = undefined> = (event: E, ctx: ExtensionContext) => Promise<R | void> | R | void;
```

- 异步 handler **全部被 await**，`for...of` **串行**，不并发。
- 顺序 = 扩展加载顺序 → 扩展内注册顺序。
- 例外：`session_shutdown` 用 `Promise.all` **并行**执行。

### 3.2 ⚠️ 两个超时预算差 15 倍

| 常量 | 值 | 来源 |
| --- | --- | --- |
| `EXTENSION_HANDLER_TIMEOUT_MS` | **30_000** | `[源码 extensions/runner.ts:81]` |
| `SESSION_SHUTDOWN_HANDLER_TIMEOUT_MS` | **2_000** | `[源码 extensions/runner.ts:101]` |

`session_shutdown` 只有 **2 秒**（源码注释说明：不能让扩展卡住 Ctrl+C / `/exit`）。
**任何在 shutdown 里 await 超过 2s 的操作都会被 race 掉，其后的 `finally` 清理不保证执行 → 子进程变孤儿。**

### 3.3 ⚠️ 错误语义不对称：普通事件 fail-open，tool_call fail-closed

| 路径 | handler 抛错 | handler 超时 |
| --- | --- | --- |
| 通用 `emit()` | 吞掉 → 记 `emitError` → 返回 `undefined`（**fail-open**） | 同上，fail-open |
| `emitToolCall()` | `{block:true, reason:"Extension <path> failed: ..."}` | `{block:true, reason:"... timed out after 30000ms"}` |

已核对 `[源码 extensions/runner.ts:1082-1137]`，源码注释原文：
> On-timeout policy: **fail-closed**… an unresponsive extension MUST NOT be treated as silent consent to run the tool.

这对 Guard 是**免费的兜底**：Bridge 挂死时平台自动拦截。但 30s 才触发，所以业务侧仍须自带更短超时（见 §6.3）。

### 3.4 可拦截事件一览

| 事件 | 返回值 | 效果 |
| --- | --- | --- |
| `tool_call` | `{block?, reason?, input?}` | 唯一能阻止工具执行的 |
| `session_before_switch/branch/compact/tree` | `{cancel?: true}` | 取消 |
| `input` | `{handled?: true, text?, images?}` | 接管用户输入 |
| `user_bash` / `user_python` | `{result}` | 接管执行 |
| `session_stop` | `{continue:true, additionalContext}` 或 `{decision:"block", reason}` | 续轮/阻止 |
| `tool_result` | `{content?, details?, isError?}` | **中间件式链式**，后续 handler 看到前面的修改 |

`session_stop` 注意：连续续轮上限 8 次，且**对 task/subagent 会话永不触发** `[文档 extensions.md]`。

---

## 4. Tool 注册

### 4.1 ⚠️⚠️ 最大的坑：两套 API 的 `execute` 参数顺序不同

这是本次调研发现的**最危险的一处**，两篇官方文档互相矛盾。已逐一核对源码定案：

| 场景 | `execute` 签名 | 依据 |
| --- | --- | --- |
| **Extension `pi.registerTool()`**（本项目使用） | `(toolCallId, params, `**`signal, onUpdate`**`, ctx)` | `[源码 extensibility/extensions/wrapper.ts:340]` + `[源码 extensions/types.ts:575-581]` + `[文档 extensions.md]` |
| Custom Tool（`.omp/tools` 文件发现 / SDK `customTools`） | `(toolCallId, params, `**`onUpdate, ctx, signal`**`)` | `[源码 extensibility/custom-tools/wrapper.ts:37]` + `[文档 custom-tools.md]` |

**第 3 位与第 5 位互换**。TS 类型在各自体系内都是自洽的，所以**错用不会报编译错**——照着 `custom-tools.md` 写 extension tool，会把 `onUpdate` 当 `signal` 用，运行时才炸。

本项目用的是 extension 路径，正确写法：

```ts
pi.registerTool({
  name: "dc_query",
  label: "DC Query",
  description: "...",
  parameters: pi.zod.object({ ... }),
  loadMode: "essential",
  approval: "read",
  async execute(_toolCallId, params, signal, onUpdate, ctx) { ... },
});
```

> 这也是本项目决策"Custom Tool 由 Extension 通过 `pi.registerTool()` 注册，不用 `.omp/tools` 文件发现"的额外收益：只需守住一套签名。

### 4.2 ⚠️ `loadMode` 默认是 `discoverable`，不是顶层

`[源码 extensions/types.ts:560-561]` 注释原文："Extension tools default to `"discoverable"`; set `"essential"` to stay top-level."

后果：开启工具发现模式（`tools.discoveryMode` / `tools.xdev`）后，扩展工具被降级到 BM25 发现层，**模型默认看不到**。若你的工具描述里写着"模型必须总是查询此工具"，模型想遵守也够不着。

**规范：凡是"模型必须能随时调用"的工具，显式声明 `loadMode: "essential"`。**

### 4.3 `approval` 默认是最严的 `exec`

`[源码 extensions/types.ts:564-566]`：未声明 `approval` 时按 `"exec"` 处理。只读工具应显式标 `"read"`，否则在 `always-ask`/`write` 模式下会无谓地弹确认。

### 4.4 工具枚举 API 返回字符串数组

`[源码 extensions/types.ts:1267,1270]`：

```ts
getActiveTools(): string[];
getAllTools(): string[];
```

不是对象数组。判断"是否注册成功"用 `getAllTools()`；`getActiveTools()` 只反映当前激活集。

### 4.5 其他可选字段

`hidden`、`defaultInactive`、`deferrable`、`strict`、`mcpServerName`、`mcpToolName`、`renderCall`、`renderResult`、`onSession`、`formatApprovalDetails`。
影子内置工具时，`ctx.invokeTool?.(params, opts)` 可委托给同名原生实现（仅同名，不能跨工具提权）。

---

## 5. 审批模型

### 5.1 三种模式 `[文档 approval-mode.md]`

| 模式 | 自动批准 | 提示 |
| --- | --- | --- |
| `always-ask` | `read` | `write`, `exec` |
| `write` | `read`, `write` | `exec` |
| `yolo`（**默认**） | 全部 | 无 |

### 5.2 执行顺序（关键）

```
① tools.approval.<tool> == "deny"  → 直接抛错，tool_call 根本不发出
② 发出 tool_call → 扩展 Guard（可 block / 可改 input）
③ 平台审批门（对修订后的入参求值）
④ 真正执行
```

**结论 1**：不存在"平台已批准就跳过扩展 Guard"——Guard 在审批门**之前**，`yolo` 也不跳过。
**结论 2**：反向陷阱存在——用户配了 `tools.approval.<tool>: deny` 时你**收不到 `tool_call` 事件**，审计日志会缺这一条。
**结论 3**：默认是 `yolo`。**永远不要把平台审批当作写保护**，Guard 必须自成闭环。
**结论 4**：子代理强制 `yolo` 且无 UI，但扩展仍加载，Guard 照样跑——这正是 fail-closed 的价值。

---

## 6. tool_call Guard（本项目安全核心）

### 6.1 ⚠️⚠️ 不要自己解析 edit 的目标路径

平台已经替你算好了。`[源码 extensibility/tool-event-input.ts:59-80 normalizeToolEventInput]` 会向 `event.input` 注入派生字段：

- hashline 单目标 → 同时补 `path` 和 `paths`
- **hashline 多目标 → 只有 `paths`（数组），`path` 不存在**
- replace/patch 模式 → 从 `_path` 传播到 `path`

且它**刻意拒绝信任模型自填的 `_path`**，源码注释：
> Trusting a passthrough `_path` here would let a model-supplied field override the real edit target and **bypass extension gates that allowlist by path**.

已核实该归一化覆盖**主发射路径**（`[源码 session/agent-session.ts:3134]`）与 wrapper 补发路径（`wrapper.ts:211,355`），所以 `event.input.path/paths` 在所有路径下都可靠。

hashline 的真实格式是**行首 `¶PATH#TAG`**（`[源码 tool-event-input.ts:1]` `HASHLINE_FILE_PREFIX = "¶"`），不是方括号语法。

**规范写法**：

```ts
const targets = [
  ...(typeof input.path === "string" ? [input.path] : []),
  ...(Array.isArray(input.paths) ? input.paths.filter(p => typeof p === "string") : []),
];
if (targets.length === 0) return { block: true, reason: "无法确定写入目标，拒绝" }; // fail-closed
```

> 注：官方示例 `examples/hooks/protected-paths.ts` 只读 `input.path`，在多文件 hashline edit 下会漏判。**不要照抄这个示例。**

### 6.2 ⚠️ 类型收窄必须用官方 type guard

`event.toolName === "bash"` **无法**收窄类型（`CustomToolCallEvent.toolName: string` 与所有字面量重叠）。用 `[源码 extensions/types.ts:946+]` 导出的：

```ts
import { isToolCallEventType } from "@oh-my-pi/pi-coding-agent";
if (isToolCallEventType("bash", event)) { event.input.command; /* string */ }
```

### 6.3 超时不等式（必须守住）

```
Bridge 业务超时  <  EXTENSION_HANDLER_TIMEOUT_MS (30s)
```

否则拒绝理由会从业务错误退化成 "Extension timed out"，且 agent loop 白卡 30 秒。当前 guard 用 10s，合规。

### 6.4 黑名单 vs 白名单

当前守护 `edit/write/ast_edit/bash` 四个。但仍能造成写入或代码执行的还有：`eval`、`task`（拉子代理后在子会话自由写）、`memory_edit`、`computer`、`checkpoint`、`rewind`、`hub`、`browser`、`manage_skill`、`learn`，以及全部 MCP 工具（前缀 `mcp__`）。

**建议改为白名单放行**（只对 `read/grep/glob/ast_grep/todo/...` 直接 return，其余送 Runtime 裁决）。黑名单在这个安全模型下天然滞后于平台演进。

### 6.5 无 UI 时必须显式 fail-closed

`ctx.hasUI === false`（print / RPC / **子代理**）时 `ctx.ui.confirm()` 直接返回 false 或不可用。凡是依赖人类确认的路径，headless 下必须拒绝，而不是静默放行。

---

## 7. Slash Command

```ts
pi.registerCommand("dc", {          // 不带斜杠
  description: "...",
  getArgumentCompletions: (prefix) => [...] | null,
  handler: async (args: string, ctx: ExtensionCommandContext) => { ... },
});
```

### 7.1 ⚠️ 三个反直觉点

1. **`args` 是裸字符串**：只按第一个空格切一刀，未做 shell 分词、未去引号。`/dc plan "a b"` → `args === 'plan "a b"'`。子命令自己解析。
2. **返回值被完全丢弃**：`handler` 返回 `Promise<void>`。**不能靠 return 注入 prompt**（这点与 TS custom command 不同）。要影响会话必须主动调 `pi.sendUserMessage(...)` / `pi.sendMessage(...)` / `pi.appendEntry(...)`。
3. **抛错被静默吞掉**：只记 `emitError`，用户什么都看不到。自己 `try/catch` + `ctx.ui.notify(msg, "error")`。

### 7.2 优先级与命令上下文

扩展命令在 prompt 管线里**第 1 顺位**（早于 TS custom command、文件 md 命令、prompt 模板）。

`ExtensionCommandContext` 比普通 ctx 多：`waitForIdle()`、`newSession()`、`switchSession()`、`branch()`、`navigateTree()`、`reload()`、`compact()`。改会话状态前先 `await ctx.waitForIdle()`。

---

## 8. Skill

- 布局：`<root>/<skill-name>/SKILL.md`，**严格一层，非递归**。`skills/group/x/SKILL.md` 不会被发现。
- 项目级 `.omp/skills/`；用户级 `~/.omp/agent/skills/`。
- **⚠️ native `.omp` provider 要求 frontmatter 必须有 `description`，缺了会被静默丢弃。**
- `name` 可选，默认取目录名。其他可选：`globs`、`alwaysApply`、`hide`、`disableModelInvocation`。
- `hide: true` **不禁用** skill，只是不进 system prompt 列表，仍可经 `skill://<name>` 访问。
- 去重键是 skill **name**，first-wins，provider 按 priority：`native`(100) > `omp-plugins`(90) > `claude`(80) > …
- 过滤顺序：`disabledExtensions` 含 `skill:<name>` → source 开关 → `ignoredSkills`(glob 排除) → `includeSkills`(glob 白名单)。glob 匹配的是 **skill 名**，不是路径。

扩展想自带 skill 目录而不污染用户 `.omp/skills/`，可监听 `resources_discover` 返回 `{skillPaths:[...]}`。
**注意**：`[文档 extensions.md]` 说明 `emitResourcesDiscover(...)` 已实现，但当前代码库中**没有 AgentSession 调用点** → 该路径目前实际上不生效。`[未验证 是否有其他触发点]`

---

## 9. 子代理（task）

### 9.1 ⚠️⚠️ 每个子代理都会重跑你的扩展工厂并触发 `session_start`

已核实 `[源码 task/executor.ts:3097-3152]`：子会话有自己的 `extensionRunner`，会 `initialize(...)` 并 `emit({type:"session_start"})`。

**对本项目是重大影响**：`session_start` 里 `bridge.ensureStarted()` 意味着
**N 个子代理 = N 个 `python -m runtime.omp_bridge` 进程**，且子会话 shutdown 时机不受主会话控制，叠加 §3.2 的 2s 预算极易堆积僵尸进程。

对策（择一）：
- 模块级按 `repoRoot` 做 BridgeClient 单例 + 引用计数；
- 或改为纯懒启动（去掉 `session_start` 里的预热），只在首次 `request()` 时拉起。

### 9.2 其余要点

- `ExtensionAPI` 上**没有** `task()`/`spawn()` 方法。从扩展发起子代理的稳妥做法是注册工具/命令引导模型去调内建 `task` 工具（能吃到并发信号量、注册表、`agent://` 产物）。底层 `pi.pi.runSubprocess()` 属内部 API，无稳定性承诺。
- 隔离模式由 `task.isolation.mode` 控制。**`mode: none` 时 `isolated` 参数根本不在 schema 里**。Windows 实际后端是 ProjFS，`auto` 会沿候选链回退，最差退化为递归拷贝。需要 git 仓库。
- isolated 子代理完成即拆除，状态 `parked` 且不可复活，只剩 `history://<id>`。
- **子代理要能用你的扩展工具，必须在 `.omp/agents/*.md` 的 `tools` 里点名**（给了 `tools` 就会自动补 `yield`）。
- Agent 发现：`.omp/agents/*.md` → `~/.omp/agent/agents/*.md` → plugin → bundled，first-wins、大小写敏感。**`.claude/agents`、`.codex/agents`、`.gemini/agents` 被有意跳过**（frontmatter 契约不同）。
- 结构化输出优先级：单次调用 `outputSchema` > agent frontmatter `output` > 继承父会话。结果在 `details.results[]`；输出截断 500KB / 5000 行，全文在 `agent://<id>`。

---

## 10. 配置与设置

### 10.1 优先级

```
内建默认 < ~/.omp/agent/config.yml < <cwd>/.omp/config.yml < --config 覆盖层 < 运行时 flag
```

### 10.2 ⚠️ 两套相反的目录查找规则，别记混

| 对象 | 规则 |
| --- | --- |
| **设置**（`.omp/config.yml`） | **只看进程 cwd 的 `.omp/`，不向上遍历祖先目录** |
| **上下文文件**（`.omp/AGENTS.md`） | **从 cwd 向上走到仓库根，取最近的非空 `.omp/`** |

另：所有写操作（`omp config set`、`/settings`）**一律写全局** `config.yml`，永不写项目文件。项目级覆盖只能手工编辑。

### 10.3 扩展怎么读配置

`ExtensionContext` 上**没有 `settings` 字段**。可用途径：
1. `pi.pi.settings.get("tools.approvalMode")`（包导出的单例 Proxy，cwd 绑定 `getProjectDir()`，子代理/多 cwd 下未必等于 `ctx.cwd`）
2. 扩展私有配置：自己读 `<ctx.cwd>/.omp/<name>.yml`，自己实现层级合并
3. `pi.registerFlag(...)` + `pi.getFlag(...)`

`.omp/RULES.md` 会变成 always-apply 的 sticky rule（长会话不丢），适合放硬性工程约束。

### 10.4 cwd 来源

`ExtensionAPI` 不暴露 cwd，加载期只能用 `process.cwd()`（可接受）。但 `ExtensionContext` 带 `cwd`，子代理 / `switchSession` 后可能与进程 cwd 不同。**建议在 `session_start` 里用 `ctx.cwd` 校正一次 stateDir。**

---

## 11. 避坑清单（速查）

| # | 坑 | 规范 |
| --- | --- | --- |
| P1 | `.gitignore` 写 `.omp/` 导致扩展静默消失 | 只忽略 `.omp/dc-state/` 这类具体子目录 |
| P2 | extension tool 与 custom tool 的 `execute` 参数顺序不同 | extension 用 `(id, params, signal, onUpdate, ctx)` |
| P3 | `loadMode` 默认 `discoverable`，模型看不到工具 | 关键工具显式 `loadMode: "essential"` |
| P4 | `approval` 默认 `exec` | 只读工具显式 `approval: "read"` |
| P5 | `session_shutdown` 只有 2s | 只发信号不等握手；`process.on("exit")` 兜底 |
| P6 | 裸 `setInterval` 抛错拆毁整个会话 | 用 `ctx.setInterval` / `ctx.clearTimer` |
| P7 | 自己解析 edit 路径 | 读 `input.path` + `input.paths`，两者皆空则 block |
| P8 | `toolName === "bash"` 无法收窄类型 | 用 `isToolCallEventType()` |
| P9 | 把平台审批当写保护 | 默认 `yolo`；Guard 必须自成闭环 |
| P10 | `tools.approval.<tool>: deny` 时收不到 `tool_call` | 审计日志需注明该盲区 |
| P11 | slash command `args` 未分词、返回值被丢弃、抛错被吞 | 自己解析 + `sendUserMessage` + `try/catch` |
| P12 | skill 缺 `description` 被静默丢弃 | native provider 下 `description` 必填 |
| P13 | 子代理重跑扩展工厂 → N 个 Python 进程 | BridgeClient 单例 + 引用计数，或纯懒启动 |
| P14 | 设置不向上查找、上下文文件向上查找 | 两套规则相反 |
| P15 | Bridge 超时 ≥ 30s 会退化成平台超时 | 守住 `业务超时 < 30s` |
| P16 | 加载期做副作用 | 工厂内只注册 |

---

## 12. 本项目当前已确认的偏差

以下均已核对源码，**不是猜测**。按严重度排序。

### 12.1 必须修

| # | 位置 | 问题 | 依据 |
| --- | --- | --- | --- |
| D1 | `guards.ts:9,43-46` | edit 路径正则用 `[path#abcd]` 方括号语法，官方是行首 `¶PATH#TAG` → 正则**永不命中**，`paths` 恒为 `[]` → 对 `edit` 实质放行（fail-open） | `[源码 tool-event-input.ts:1,44-56]` |
| D2 | `commands.ts:94-99` | `getAllTools()` 按对象数组用（取 `.name`），实际返回 `string[]` → `JSON.stringify` 出带引号字符串 → `startsWith("dc_")` 恒 false → doctor 的 `custom_tools` 检查从未真正执行；且代码注释把此自身 bug 归因为"平台不支持枚举"，会误导后续维护者 | `[源码 extensions/types.ts:1267,1270]` |
| D3 | `session.ts:21` | `save_snapshot` 用 5s 超时，`session_shutdown` 预算只有 2s → handler 被 race 掉，`finally` 里的 `bridge.stop()` 不保证执行 → Python 子进程变孤儿 | `[源码 extensions/runner.ts:101]` |
| D4 | `tools.ts` 全部 6 个 `registerTool` | 缺 `loadMode: "essential"` → 工具发现模式下 dc_* 被降级，模型默认够不着；与 `dc_query` 描述里"必须总是查询此工具"矛盾 | `[源码 extensions/types.ts:560-561]` |

D1 的正确修法不是修正则，而是**删掉自己的解析**，直接读平台注入的 `input.path` / `input.paths`（见 §6.1）。

### 12.2 建议修

- **D5** `index.ts:15` 每个子代理会话各自 `new BridgeClient` → 多 Python 进程（§9.1）。
- **D6** `guards.ts:8` 黑名单未覆盖 `eval`/`task`/`memory_edit`/MCP 工具等写入路径（§6.4）。
- **D7** `bridge.ts:107` stdin 无 `error` 监听，子进程死后 EPIPE 可能掀掉整个 OMP 进程；`proc.stdin.writable` 预检存在 TOCTOU 窗口。
- **D8** `bridge.ts:37` 用 `DC_PYTHON ?? "python"`，而 `commands.ts:77` doctor 硬编码 `"python"` → 设了 `DC_PYTHON` 时 doctor 检查的不是实际解释器，PASS 无意义。Windows 上 `python` 还可能命中 Store 存根。
- **D9** `commands.ts:161` `hasUI === false` 时 `/dc approve` **跳过确认直接派发** `GRANT_APPROVAL`。审批是设计里唯一的人类决策点，headless 下应拒绝而非静默放行。
- **D10** `renderers.ts` 对 `unknown` 直接取下标/`?? []`，Bun 只转译不做类型检查所以运行正常，一旦接入 `tsc --noEmit` 会全线飘红。
- **D11** 目录名 `develoip-copilot` 拼写错误（`develop` 少了 p、多了 i），且它会成为扩展显示名（`getExtensionNameFromPath`）。README 标题同样是 `develoip-copilot`。建议统一更名为 `develop-copilot`——**这是破坏性重命名，需同步 `.omp/skills/`、docs 引用与 git 历史，请确认后再动**。

### 12.3 易碎点（当前正确，但极易被改坏）

- **F1** `bridge.ts:46-87` `ensureStarted()` 从 `if (this.proc) return` 到 `this.proc = proc` 之间**一个 await 都没有**（`mkdirSync`/`spawn` 均同步），靠 JS 单线程保证不重复 spawn。只要有人把 `mkdirSync` 改成 `await fs.promises.mkdir`，立刻变成并发多 spawn 且旧进程泄漏。**建议加显式 `startingPromise` 串行化。**
- **F2** `guards.ts:59` 的 10s 与平台 30s 的不等式是刻意的（§6.3），改超时数字时务必守住。
- **F3** `index.ts` 的"纯注册"性质（§2.1）。
- **F4** `bridge.ts:58` 已设 `PYTHONIOENCODING`/`PYTHONUTF8`，Python 侧 `omp_bridge.py:314-324` 每帧 `flush()`——**缓冲与编码问题已闭环**，改任一端时需同步。加 `-u` 可作额外防御。

### 12.4 待确认

1. `ctx.ui.notify` 在 `omp -p` / RPC 模式下的实际落地（各 mode 自有实现）。若 `/dc status` 需在 headless 可见，可能应改走 `pi.sendMessage()`。
2. `bridge.ts:98-101` 超时只在 TS 侧删 pending，未向 Python 发取消 → Runtime 长操作可能已写入 Event Store，而 TS 侧报 `BRIDGE_TIMEOUT`（对 guard 等同拒绝）。这是"不确定态"而非干净的 fail-closed，取决于是否存在这类长写操作。
3. 子代理内判别"我是子代理"的权威字段（用于 D5 的单例判断）。

---

## 13. 验证方式

```bash
# 平台侧
omp read "omp://"                    # 官方文档索引（122 篇）
omp read "omp://extensions.md"       # 权威规范
git check-ignore -v .omp/extensions/develoip-copilot/index.ts   # 必须无输出（P1）

# 项目侧
python -m pytest -q
python -m compileall -q runtime roles tools adapters fixtures tests
bun tests/omp/smoke.ts
git diff --check
```

会话内验证（需在加载了本扩展的 OMP 会话中执行）：`/dc doctor`、确认 dc_* 工具可被模型调用、构造越权写入确认 Guard 拦截。

**排障顺序**：扩展没生效 → 先查 gitignore（P1）→ 再查入口形态（§1.1）→ 再查 `disabledExtensions` → 最后看 `.omp/dc-state/bridge.stderr.log`。
