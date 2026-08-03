# develoip-copilot 设计到实现追踪表

> 文档用途：追踪设计要求到具体实现的映射关系
> 适用对象：实施者、代码评审者、质量保障
> 更新频率：每个实现任务完成后更新

---

## 追踪原则

1. **当前 Milestone 的验收要求必须进入追踪表**
2. **每条设计要求必须追踪到具体的实现位置**
3. **验证方式必须可执行、可验收**
4. **状态必须真实反映实施进度**
5. **架构不变量由 `docs/design-constraints.md` 审计**

---

## 设计要求稳定 ID

| ID | 描述 | 设计章节 |
|----|------|---------|
| ARCH-01 | 不创建主控 Agent | design.md §5.3 |
| ARCH-02 | 顶层 Skill 对应用户任务 | design.md §6 |
| ARCH-03 | 多 Agent 流程写入 Skill Procedure | design.md §1.1 #2, §7.4 |
| ARCH-04 | 专业角色实现为 `.omp/agents/*.md` | design.md §8 |
| ARCH-05 | 确定性能力首选独立 Python CLI | design.md §10 |
| ARCH-06 | Python CLI 不强制注册为 Custom Tool | design.md §10.8 |
| ARCH-07 | Agent 输出引用只用于临时交接 | design.md §9.2-9.3 |
| ARCH-08 | 正式产物写入文件系统，长期状态写入 `.project/` | design.md §11.2-11.4 |
| ARCH-09 | 首版不默认使用 Hub | design.md §9.5 |
| ARCH-10 | 不重新引入通用平台能力 | design.md §3, §20 |
| SKILL-01 | SKILL.md 必需章节 | design.md §7.1 |
| SKILL-02 | When to use 明确触发 | design.md §7.2 |
| SKILL-03 | Do not use 定义排除 | design.md §7.3 |
| SKILL-04 | Procedure 定义流程 | design.md §7.4 |
| SKILL-05 | Delegation 明确责任 | design.md §7.5 |
| SKILL-06 | Failure handling 定义失败处理 | design.md §7.6 |
| M1-01 | OMP 能发现三个 Skill | design.md §17 MS1 |
| M1-02 | OMP 能通过 `task` 解析并调用三个 Agent | design.md §17 MS1 |
| M1-03 | Skill 内 references 可以成功读取 | design.md §17 MS1 |
| M1-04 | Skill Procedure 能串联两个 Agent | design.md §17 MS1 |
| M1-05 | Agent 输出能被主会话继续消费 | design.md §17 MS1 |
| M1-06 | Python Tool 能被 Skill 流程调用 | design.md §17 MS1 |
| M1-07 | 一次 Agent 失败能被明确报告 | design.md §17 MS1 |
| M1-08 | 一次不完整输入能被正确阻断 | design.md §17 MS1 |
| SAFE-01 | 正式修改前确认 | design.md §13.2 |
| SAFE-02 | 隔离执行 | design.md §13.3 |

---

## 追踪表（Milestone 1）

| ID | 设计要求 | 实现位置 | 验证方式 | 状态 | Owner | Evidence | Notes |
|----|---------|---------|---------|------|-------|----------|-------|
| M1-01 | OMP 能发现三个 Skill | .omp/skills/ | 发现 smoke test | TODO | | | |
| M1-02 | OMP 能通过 `task` 解析并调用三个 Agent | Skill Procedure + task | 调用 smoke test | TODO | | | |
| M1-03 | Skill 内 references 可以成功读取 | Skill references | 读取测试 | TODO | | | |
| M1-04 | Skill Procedure 能串联两个 Agent | Skill Procedure | 流程测试 | TODO | | | |
| M1-05 | Agent 输出能被主会话继续消费 | Skill Procedure | 交接测试 | TODO | | | |
| M1-06 | Python Tool 能被 Skill 流程调用 | Skill Procedure | 调用测试 | TODO | | | |
| M1-07 | 一次 Agent 失败能被明确报告 | Skill Procedure | 失败场景测试 | TODO | | | |
| M1-08 | 一次不完整输入能被正确阻断 | Skill Procedure | 阻断测试 | TODO | | | |

---

## 状态定义

- **TODO**: 未开始实施
- **WIP**: 实施中
- **VERIFY**: 实现完成，待验证
- **PASS**: 验收通过
- **FAIL**: 验收未通过
- **BLOCKED**: 被阻塞
- **N/A**: 不适用当前 Milestone

---

## 实施前检查

每个实施任务开始前，必须：

1. 在追踪表中找到对应的设计要求
2. 确认验证方式已定义
3. 更新状态为 WIP
4. 记录实现位置

## 实施后更新

每个实施任务完成后，必须：

1. 更新实现位置（如具体文件路径）
2. 运行验证方式
3. 更新状态（PASS/FAIL/VERIFY/N/A）
4. 如未通过，记录原因并修正

---

## Milestone 1 适用约束

以下架构不变量在 Milestone 1 中适用，但对应验证可能标记为 N/A：

| ID | 描述 | M1 验收状态 | 说明 |
|----|------|-------------|------|
| ARCH-01 | 不创建主控 Agent | PASS（审计） | 不创建 orchestrator 等 |
| ARCH-02 | 顶层 Skill 对应用户任务 | PASS（审计） | 三个 Skill 有最小 Procedure |
| ARCH-03 | 多 Agent 流程写入 Skill Procedure | PASS（审计） | 最小 Procedure 验证 OMP 编排 |
| ARCH-04 | 专业角色实现为 `.omp/agents/*.md` | PASS（审计） | 三个 Agent 配置正确 |
| ARCH-05 | 确定性能力首选独立 Python CLI | PASS（审计） | hello CLI 可独立运行 |
| ARCH-06 | Python CLI 不强制注册为 Custom Tool | N/A | M1 不注册 Custom Tool |
| ARCH-07 | Agent 输出引用只用于临时交接 | PASS（测试） | Batch 5 验证临时交接 |
| ARCH-08 | 正式产物写入文件系统，长期状态写入 `.project/` | N/A | M1 不产生正式工程修改 |
| ARCH-09 | 首版不默认使用 Hub | PASS（审计） | 不使用 Hub |
| ARCH-10 | 不重新引入通用平台能力 | PASS（审计） | 未引入 Runtime 等 |
| SKILL-01 | SKILL.md 必需章节 | PASS（审计） | 模板包含必需章节 |
| SKILL-02 | When to use 明确触发 | PASS（审计） | 明确限制为 smoke 场景 |
| SKILL-03 | Do not use 定义排除 | PASS（审计） | 明确排除真实工程请求 |
| SKILL-04 | Procedure 定义流程 | PASS（测试） | 最小 Procedure 可执行 |
| SKILL-05 | Delegation 明确责任 | PASS（测试） | 最小 Delegation 可用 |
| SKILL-06 | Failure handling 定义失败处理 | PASS（测试） | Batch 5 验证失败处理 |
| SAFE-01 | 正式修改前确认 | N/A | M1 不进行正式工程修改 |
| SAFE-02 | 隔离执行 | N/A | M1 不产生正式工程修改 |

---

## 真实案例需求

除设计要求外，真实案例使用中发现的必须支持的功能也应记录在此：

| 需求来源 | 需求描述 | 实现位置 | 验证方式 | 状态 | Owner | Evidence | Notes |
|---------|---------|---------|---------|------|-------|----------|-------|
| | | | | | | | |

真实工程样例存储位置：
- `fixtures/` - 可提交、可重复、预期明确的小型样例
- `real-samples/` - 默认本地或脱敏后的真实案例
- `evals/` - case 定义、rubric 和结果

---

## 版本

- v1.2: 2026-08-03, 修正追踪原则，增加 Milestone 1 适用约束
- v1.1: 2026-08-03, 清理多余 Milestone 展开，只保留 Milestone 1
- v1.0: 2026-08-03, 基于 design.md v2.1 冻结版本初始化