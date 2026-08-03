# Milestone 2 Validation Report

> 里程碑：Milestone 2 — QSPI Vertical Slice Implementation
> 结果：EXECUTED / FROZEN
> 语义权威：[execution-contract.md](execution-contract.md)
> 起始分支：`base/develop`
> Milestone 2 起始 commit：`9192a740d20fbe30d48df0c033f30001c21a0cdc`
> Milestone 2 功能冻结 commit：`157764b61f8a97d6c2fdeaf5e15dde7c1ed44363`
> 收尾提交：`d2a9ad8a70851fab7402c08c51cbfb80e75218cc`（仅 `.gitignore`、缓存索引清理与本报告修正；无 Runtime/测试行为变化）
> 远程分支：`origin/base/develop` 与当前 `base/develop` 同步

## 1. 实现范围

已实现：

- `runtime.core.Runtime`：Command Dispatch、Ownership、状态迁移、事件生成、派生结果和 Restore；
- `runtime.persistence.JsonlEventStore`：append-only JSONL、sequence、幂等和损坏拒绝；
- Schema v1：12 个核心对象的稳定 ID、对象类型、版本和枚举校验；
- Risk/Approval/Baseline/Evidence/Claim/Acceptance/Waiver/Blocker/Closure Gate；
- Role Invocation Layer 和结构化 Tool 边界；
- OMP/pi 薄适配层；
- 自包含 QSPI fixture：Baseline A 缺陷、Baseline B 修复、Verilog 模块、输入、期望结果、testbench 和独立 Python reference；
- 5 个最小 Skill 方法文档；
- 实现决策和验证报告。

未实现且明确延期：

- 真实板卡状态修改和回滚；
- 模块/接口级 Scope 冲突算法；
- 数据库服务、Web UI、完整 OMP/pi 产品化和通用工作流 DSL。

## 2. 验证命令和结果

### 2.1 自动化测试

```text
python -m pytest -q
41 passed
```

该结果是本地工作区执行证据；当前仓库没有配置独立 CI，因此没有独立 CI 复验结论。

其中：

- 24 个契约场景均有可追踪测试编号；
- 8 个跨模型组合场景均有可追踪测试编号；
- Schema/Persistence/Runtime/Role/Tool/Adapter/Fixture/E2E 测试全部通过。

### 2.2 编译检查

```text
python -m compileall -q runtime roles tools adapters fixtures tests
PASS
```

### 2.3 QSPI fixture

Baseline A：

```text
actual=873625686 (0x34127856)
expected=305419896 (0x12345678)
passed=false
```

Baseline B：

```text
actual=305419896 (0x12345678)
reference=305419896 (0x12345678)
passed=true
independent_check_passed=true
```

### 2.4 Adapter 指定回归

OMP/pi Adapter 已覆盖计划指定的：

```text
S03 / S06 / S13 / S20 / S24
```

结果：通过。Adapter 未建立第二套 Task 状态，也未提供 Derived Result 直接写入口。

## 3. Milestone 2 Gate 结果

| Gate | 结果 | 证据 |
| --- | --- | --- |
| Gate A：Runtime 骨架 | PASS | Schema、Persistence、Runtime tests |
| Gate B：契约一致性 | PASS | 24 场景、8 组合场景、Reject/Derived Result tests |
| Gate C：执行边界 | PASS | Role/Tool/Approval/Adapter tests |
| Gate D：QSPI 纵向样板 | PASS | QSPI success、verification failure、approval revoke、conflict、restore tests |
| Gate E：冻结门禁 | PASS | 本报告、全量回归、开放决策状态 |

关键闭环已验证：

- Command 是唯一写入口；直接写 Gate/Claim/Closure/Project Status 被拒绝；
- Risk 激活使旧 Approval 失效并进入 `AWAITING_APPROVAL`；
- Approval 撤销使正式写入停止并将 Artifact 标记为待审查；
- Baseline A→B 传播到 Evidence、Claim 和 Approval；
- Handoff Acceptance 不改变技术 Acceptance；
- Acceptance 与 Waiver 分离；
- 验证反证进入 `CONTRADICTED` 并阻止 Closure；
- Snapshot 与完整 Event replay 的结果一致；
- QSPI 成功路径必须经过独立验证、Reviewer Acceptance、record gate 和显式关闭。

## 4. 记录和工作区边界

`RuntimeEvent` 与长期 Record 分离。测试验证了 Record `written`、`declined` 路径；普通命令、完整聊天历史和原始日志不自动生成长期 Record。

Milestone 2 实现已存在于远程 `base/develop` 分支，当前冻结候选 commit 为 `157764b61f8a97d6c2fdeaf5e15dde7c1ed44363`。本次修正尚未创建新的提交、branch、PR 或 push；真实设备写操作仍未执行。缓存文件仅从 Git 索引移除，本地生成文件保留。

## 5. 剩余限制与后续入口

本阶段关闭的是 QSPI fixture 纵向运行能力，不是生产工程中的全部 QSPI Bug，也不是真实板级验证结论。进入下一阶段前应优先：

1. 将最小 Runtime 接入实际 OMP/pi 运行环境并保持 Adapter 回归；
2. 若需要真实板卡，先单独完成 OI-11 授权、回滚和外部 Validator 评审；
3. 若需要更细 Scope，再扩展 OI-04，但不得改变当前 Scope 冲突拒绝语义。
