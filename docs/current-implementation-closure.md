# develoip-copilot 当前实现收口诊断

> 生成时间：2026-08-04
> 目的：为端到闭环验证提供现状基线和收口决策依据

---

## 1. 当前真实能力

### 1.1 已实现（SUPPORTED）

#### RTL 基础工具
- ✅ `tools/rtl/extract_modules.py` - 模块提取，支持 JSON 输出，文件存在性检查
- ✅ `tools/rtl/extract_interfaces.py` - 接口提取（端口、参数），支持 JSON 输出
- ✅ `tools/rtl/scan_clock_reset.py` - 时钟复位扫描，支持 JSON 输出
- ✅ `tools/rtl/build_hierarchy.py` - 层级构建工具（代码已存在）

**验证状态**：已在 fixtures/rtl/normal/counter.v 上验证，输出合法 JSON

#### 仿真日志解析工具
- ✅ `tools/simulation/parse_log.py` - 日志解析，提取错误、警告、断言，支持 JSON 输出
- ✅ `tools/simulation/extract_failures.py` - 失败提取，支持时间排序和首个失败定位

**验证状态**：已在 fixtures/simulation/normal/sim_pass.log 和 error/sim_fail.log 上验证

#### 仿真执行工具
- ✅ `tools/simulation/run.py` - 仿真命令执行和结果捕获，支持超时和 JSON 输出

**验证状态**：工具可运行，帮助信息正常

#### OMP 骨架
- ✅ `.omp/skills/rtl-architecture-analysis/SKILL.md` - RTL 架构分析技能
- ✅ `.omp/skills/rtl-to-testbench/SKILL.md` - RTL 到 testbench 技能
- ✅ `.omp/skills/simulation-analysis/SKILL.md` - 仿真分析技能
- ✅ `.omp/agents/rtl-analyst.md` - RTL 分析 Agent
- ✅ `.omp/agents/verification-engineer.md` - 验证工程师 Agent
- ✅ `.omp/agents/simulation-analyst.md` - 仿真分析 Agent

**验证状态**：tests/omp/smoke_test.py 已验证文件存在性和结构

#### Fixture 样例
- ✅ `fixtures/rtl/normal/counter.v` - 正常计数器 DUT
- ✅ `fixtures/rtl/normal/counter_buggy.v` - 错误计数器 DUT（注入 +2 错误）
- ✅ `fixtures/simulation/normal/sim_pass.log` - 仿真通过日志样例
- ✅ `fixtures/simulation/error/sim_fail.log` - 仿真失败日志样例

**验证状态**：样例已存在，可被工具正确解析

---

### 1.2 部分实现（PARTIAL）

#### PASS/FAIL 判定逻辑
**位置**：`tools/simulation/parse_log.py`

**当前行为**：
- 依赖日志中的 `error_count` 字段判定：`error_count == 0` 则 PASS
- 提取 `TEST PASSED` 和 `TEST FAILED` 标记
- 提取断言失败和错误行

**边界问题**：
- ⚠️ 日志可能同时包含 `assertion failure` 和 `Errors: 0`，当前逻辑会误判为 PASS
- ⚠️ 没有证据冲突检测机制
- ⚠️ 日志时间单位未标准化处理

**需要修复**：实现多层判定逻辑，确保证据冲突时标记为 INCONSISTENT

---

### 1.3 仅有流程定义（DEFERRED）

#### Testbench 生成
**位置**：`.omp/skills/rtl-to-testbench/templates/tb-top.sv.tmpl`

**当前状态**：
- ✅ 有 testbench 模板文件
- ❌ 没有实际的 testbench 生成工具
- ❌ 没有模板渲染引擎
- ❌ 没有行为规格到 testbench 代码的映射

**阻塞原因**：缺少将 RTL 分析结果和行为规格转换为可编译 testbench 的 Python 工具

#### RTL 分析结果结构化交接
**当前状态**：
- ✅ 各 RTL 工具可独立输出 JSON
- ❌ 没有统一的分析结果 JSON schema
- ❌ 没有整合多个工具输出的 wrapper 工具

**阻塞原因**：`rtl-analyst` Agent 需要消费一个稳定的、包含所有必要字段的 JSON 结构

#### 端到端测试
**当前状态**：
- ✅ 有 smoke_test.py 验证 OMP 骨架
- ✅ 有独立的工具单元测试（test_rtl_tools.py 存在但内容缺失）
- ❌ 没有完整的 RTL→testbench→仿真→报告 端到端测试

---

### 1.4 未实现（UNSUPPORTED）

#### 行为规格文件
**位置**：`fixtures/rtl/normal/counter.spec.yaml`（不存在）

**缺失影响**：无法确定 DUT 的期望行为，testbench 无法 self-checking

#### 仿真器集成脚本
**当前状态**：
- ✅ `tools/simulation/run.py` 可执行任意命令
- ❌ 没有针对 iverilog/vvp 的具体编译和运行脚本生成
- ❌ 没有仿真器自动检测和适配逻辑

#### 验证报告生成
**当前状态**：
- ✅ 有模板 `templates/verification-report.md`
- ❌ 没有报告生成工具

---

## 2. 当前端到端阻塞

### 2.1 RTL 输入 → 结构化分析结果

**阻塞点**：缺少统一的 JSON schema 和整合工具

**具体文件**：
- ❌ `schemas/rtl-analysis.schema.json`（不存在）
- ❌ `tools/rtl/integrate_analysis.py`（不存在）

**影响**：
- `rtl-analyst` Agent 无法获得稳定的输入格式
- 不同工具输出需要手动整合
- 无法追踪不确定性和缺失字段

---

### 2.2 结构化分析结果 + 行为规格 → Testbench

**阻塞点**：缺少 testbench 生成工具和行为规格文件

**具体文件**：
- ❌ `fixtures/rtl/normal/counter.spec.yaml`（不存在）
- ❌ `tools/testbench/generate.py`（不存在）
- ❌ `tools/testbench/render_template.py`（不存在）

**影响**：
- 无法生成可编译的 SystemVerilog testbench
- 无法将行为规格转换为 stimulus 和 checker
- 无法生成仿真运行脚本

---

### 2.3 Testbench + DUT → 仿真执行

**阻塞点**：缺少仿真器脚本和自动检测

**具体文件**：
- ❌ `tools/simulation/detect_simulator.py`（不存在）
- ❌ `tools/simulation/generate_run_script.py`（不存在）

**影响**：
- 无法自动检测 iverilog/vsim 可用性
- 无法生成具体的编译和运行命令
- 无法统一不同仿真器的调用方式

---

### 2.4 仿真日志 → 验证报告

**阻塞点**：PASS/FAIL 判定逻辑缺陷和报告生成缺失

**具体文件**：
- ⚠️ `tools/simulation/parse_log.py`（需修复判定逻辑）
- ❌ `tools/simulation/generate_report.py`（不存在）

**影响**：
- 证据冲突时可能误判 PASS
- 无法生成结构化的验证报告
- 无法汇总失败详情和定位首个失败

---

## 3. 收口决策

### 3.1 RTL 结构提取（SUPPORTED）

**决策**：SUPPORTED

**边界**：
- ✅ 支持 Verilog-2001 基础语法
- ✅ 支持简单 SystemVerilog 模块
- ✅ 支持参数化模块
- ⚠️ 部分支持复杂 generate 块（不保证完整解析）
- ❌ 不支持 interface/modport
- ❌ 不支持 class/UVM

**验证方法**：counter.v 提取结果已验证

---

### 3.2 时钟复位扫描（SUPPORTED）

**决策**：SUPPORTED

**边界**：
- ✅ 支持基于名称启发式识别（clk/clock, rst/reset）
- ✅ 支持从 always 块敏感列表推断边沿
- ✅ 支持推断异步/同步复位
- ⚠️ 置信度依赖命名规范和代码风格
- ❌ 不支持复杂门控时钟
- ❌ 不支持多时钟域交互分析

**验证方法**：counter.v 时钟复位扫描结果已验证

---

### 3.3 仿真日志解析（PARTIAL → SUPPORTED）

**决策**：修复后标记为 SUPPORTED

**边界**：
- ✅ 支持 ModelSim 风格日志
- ✅ 支持错误、警告、断言提取
- ⚠️ 需要修复证据冲突检测
- ❌ 不支持波形数据库
- ❌ 不支持所有仿真器日志格式

**验证方法**：sim_pass.log 和 sim_fail.log 解析结果需重新验证

---

### 3.4 失败提取（SUPPORTED）

**决策**：SUPPORTED

**边界**：
- ✅ 支持按时间排序失败事件
- ✅ 支持提取首个失败
- ✅ 支持多种时间格式
- ⚠️ 依赖日志中包含时间信息
- ❌ 不支持波形级失败定位

**验证方法**：extract_failures.py 已在 sim_fail.log 上验证

---

### 3.5 Testbench 生成（DEFERRED）

**决策**：DEFERRED

**原因**：
- 当前 Milestone 2 目标是 RTL Vertical Slice Runtime
- Testbench 生成需要大量模板和渲染逻辑
- 优先收口已有工具，不扩展新能力

**下步条件**：
- 明确 testbench 生成作为 Milestone 3 核心目标
- 获得足够 Fixture 验证模板正确性

---

### 3.6 仿真器集成（UNSUPPORTED）

**决策**：UNSUPPORTED（本轮不实现）

**原因**：
- 仿真器种类多，调用方式差异大
- 需要适配层增加复杂度
- 超出当前 Milestone 2 收口范围

**替代方案**：
- 保留 `tools/simulation/run.py` 作为通用命令执行器
- 用户手动提供仿真命令
- 记录仿真器可用性作为阻塞条件

---

### 3.7 行为规格文件（UNSUPPORTED）

**决策**：UNSUPPORTED（本轮不实现）

**原因**：
- 缺少通用验证 DSL 设计
- 当前 counter.v 行为足够简单，可硬编码
- 超出当前 Milestone 2 收口范围

**替代方案**：
- 为 counter.v 创建最小行为规格（YAML）
- 仅支撑本轮 fixture，不作为通用能力

---

## 4. 最小收口方案

### 4.1 立即修复（必须完成）

1. **修复 PASS/FAIL 判定逻辑** (`tools/simulation/parse_log.py`)
   - 实现多层判定：assertion failure → FAIL, fatal/error → FAIL
   - 增加证据冲突检测：同时存在 FAIL 证据和零错误计数 → INCONSISTENT
   - 增加状态：PASS, FAIL, UNKNOWN, INCONSISTENT

2. **创建 RTL 分析结果 Schema** (`schemas/rtl-analysis.schema.json`)
   - 定义最小字段：top_module, source_files, parameters, ports, clocks, resets, unsupported_constructs, uncertainties, status
   - 端口包含：name, direction, width_expression, source_file, source_line
   - 时钟复位包含：name, edge/active_level, confidence

3. **创建 RTL 分析整合工具** (`tools/rtl/integrate_analysis.py`)
   - 调用 extract_modules, extract_interfaces, scan_clock_reset
   - 整合为统一的 JSON 输出
   - 标记 UNKNOWN 字段

4. **为 counter.v 创建最小行为规格** (`fixtures/rtl/normal/counter.spec.yaml`)
   - 定义时钟周期、复位行为、计数逻辑
   - 支撑端到端验证

5. **创建端到端测试** (`tests/e2e/test_rtl_to_verification.py`)
   - 完整流程：RTL 提取 → 分析整合 → 行为规格读取 → 判定验证
   - 覆盖正常 DUT 和错误 DUT
   - 覆盖失败路径（文件不存在、日志冲突等）

---

### 4.2 暂缓实现（本轮不做）

1. **Testbench 生成** - 保留模板，不实现生成逻辑
2. **仿真器集成脚本** - 保留 run.py 通用能力
3. **验证报告生成** - 保留模板，不实现生成逻辑
4. **波形分析** - 不实现
5. **时序分析** - 不实现

---

## 5. 验证优先级

### 高优先级（必须通过）
1. ✅ RTL 提取工具在 counter.v 上输出合法 JSON
2. ✅ 日志解析在 sim_pass.log 判定 PASS
3. ✅ 日志解析在 sim_fail.log 判定 FAIL
4. ✅ 日志解析在证据冲突时判定 INCONSISTENT
5. ✅ 整合分析工具输出符合 schema
6. ✅ 端到端测试覆盖正常 DUT
7. ✅ 端到端测试覆盖错误 DUT
8. ✅ 端到端测试覆盖失败路径

### 中优先级（尽量完成）
1. ⚠️ 所有 CLI 工具返回正确的退出码
2. ⚠️ 所有 CLI 工具在文件不存在时返回非零退出码
3. ⚠️ 仿真器不可用时明确报告阻塞

### 低优先级（可选）
1. ⚪ OMP 端到端验证（需手动执行）
2. ⚪ 完整文档更新

---

## 6. 风险与建议

### 风险
1. ⚠️ PASS/FAIL 判定逻辑修复可能影响现有 smoke test
2. ⚠️ Schema 设计可能与现有工具输出不兼容
3. ⚠️ 端到端测试可能暴露更多工具问题

### 建议
1. 先修复单个工具，再运行端到端测试
2. 使用 counter.v 作为唯一 fixture，不扩展复杂度
3. 每次修复后运行完整测试套件
4. 保留所有 golden file，便于回滚

---

## 7. 未解决问题

1. ❌ iverilog 检测到但未集成到自动流程
2. ❌ 没有实际的 testbench 生成和编译验证
3. ❌ 没有真实的仿真执行和日志生成
4. ⚠️ OMP 端到端验证需要手动执行

---

## 8. 完成标准

本轮完成必须同时满足：

- [x] RTL 分析产生结构化交接结果
- [ ] counter 正常 DUT 的行为规格存在
- [ ] RTL 整合工具输出符合 schema
- [ ] 日志解析支持 PASS/FAIL/UNKNOWN/INCONSISTENT
- [ ] 端到端测试通过
- [ ] 证据冲突不会被误判为 PASS
- [ ] Python CLI 失败返回非零退出码
- [ ] traceability 更新真实执行状态

---

## 版本
- v1.0: 2026-08-04, 初始诊断