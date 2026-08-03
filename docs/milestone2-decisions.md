# Milestone 2 Implementation Decisions

> 状态：执行中
> 适用范围：Milestone 2 QSPI Vertical Slice Implementation
> 语义权威：[execution-contract.md](execution-contract.md)

## ADR-0001 — Runtime v1 技术基线

- **起始分支**：`base/develop`
- **起始 commit**：`9192a740d20fbe30d48df0c033f30001c21a0cdc`
- **起始工作区**：非完全干净；唯一既有未跟踪项为用户提供的 `docs/develoip-copilot-Milestone2执行计划.md`，执行过程中保留。
- **运行环境**：Windows PowerShell，Python 3.11.3，pytest 9.1.1。
- **实现语言**：Python 3.11+，优先使用标准库，不引入数据库服务。
- **类型模型**：`dataclasses`/显式字典边界；对外 Command、Event 和对象均经过 Schema v1 校验。
- **测试入口**：`python -m pytest -q`。

## ADR-0002 — Persistence

采用：

```text
Append-only JSONL Event Store
+ JSON Snapshot
+ Schema Version = 1
```

原因：仓库友好、可检查、可复制，足以覆盖本阶段的追加、回放、幂等和恢复需求。Event Store 只追加 Runtime Event；不得原地更新或删除已写事件。Snapshot 不是第二事实源，恢复时必须校验事件序列和引用。

本阶段不建设数据库服务、远程持久化服务或完整事件溯源框架。

## ADR-0003 — Runtime Boundary

公开入口为：

```text
Runtime.dispatch(command)
Runtime.query(task_id)
Runtime.restore()
Runtime.save_snapshot()
```

所有状态改变必须经过 `dispatch`。`query` 只能返回对象和派生结果；不得接受状态赋值。Role Invocation、Tool 和 OMP/pi Adapter 只能调用该边界。

## ADR-0004 — Schema v1

12 个核心对象均使用稳定 ID、`object_type`、`schema_version=1` 和显式引用。枚举直接采用 `execution-contract.md` 的值；未知枚举、缺少必填字段、错误引用类型和无法序列化的值必须拒绝。

本阶段使用 Python 字典承载物理对象，序列化为 JSON；实现层不提供第二套业务语义。

## ADR-0005 — Scope 和硬件边界

- 首版 Scope 冲突使用文件级路径规范化和重叠检查。
- QSPI fixture 为仓库内自包含样板，不复制生产工程。
- 默认不执行真实板级写操作；`HARDWARE_STATE_CHANGE` 仅支持外部 Evidence 导入。
- OI-11 延期，不作为 Milestone 2 冻结条件。

## ADR-0006 — OMP/pi Adapter

适配层只做：

```text
platform request
→ Runtime Command
→ Runtime result/events
→ optional Role Invocation
→ structured response
```

适配层不保存第二套 Task 状态、不直接写 Derived Result、不绕过 Approval。首版以进程内原型接口实现，不宣称完成完整 OMP/pi 产品化。

## Decision status

| Decision | Status | Evidence |
| --- | --- | --- |
| OI-01 Event Store | CLOSED | ADR-0002、`runtime/persistence.py`、Persistence tests |
| OI-02 Snapshot | PARTIALLY_CLOSED | ADR-0002、Restore tests；仅实现最小可验证快照 |
| OI-03 Physical Schema/ID | CLOSED | ADR-0004、Schema tests |
| OI-04 Scope conflict | PARTIALLY_CLOSED | ADR-0005、file-scope tests；模块/接口 Scope 延后 |
| OI-05 Baseline capture | CLOSED | `runtime/tools.py`、Baseline tests |
| OI-06 Evidence criteria | CLOSED | QSPI fixture tests and policy tests |
| OI-07 Approval adapter | CLOSED | `runtime/tools.py`、Approval boundary test |
| OI-08 Validator invocation | CLOSED | `runtime/roles.py`、Role boundary tests |
| OI-09 Record Gate | CLOSED | Record decision and Gate tests |
| OI-10 OMP/pi adapter | CLOSED | `adapters/omp_pi.py`、Adapter regression |
| OI-11 Board rollback | DEFERRED | 本阶段不访问真实设备 |
| OI-12 Error categories | CLOSED | `runtime/errors.py`、Reject tests |

最终状态由 [milestone2-validation-report.md](milestone2-validation-report.md) 按实际测试结果复核；本文件不替代契约。
