# develoip-copilot 端到端支持范围

> 版本：v1.0
> 日期：2026-08-04
> 目的：明确当前版本能够真实、可验证支持的 RTL 子集

---

## 支持范围定义

### 1. RTL 语言特性

#### ✅ 支持（SUPPORTED）

- Verilog-2001 基础语法
- 简单 SystemVerilog 模块声明（module ... endmodule）
- 参数化模块（parameter 和 localparam）
- 基本端口类型（input, output, inout）
- 基本数据类型（wire, reg, logic）
- 位宽声明（[WIDTH-1:0]）
- always 块（组合逻辑和时序逻辑）
- 基本运算符（+, -, &, |, ^, ~, <<, >>）
- 条件语句（if-else, case）
- 基本时序控制（posedge, negedge）

#### ⚠️ 部分支持（PARTIAL）

- generate 块（简单场景可识别，不保证完整解析）
- 函数和任务（可识别存在，不解析内容）
- 复杂表达式（基础解析，不支持复杂嵌套）

#### ❌ 不支持（UNSUPPORTED）

- SystemVerilog interface 和 modport
- SystemVerilog class 和 UVM
- SystemVerilog 跨模块引用
- 复杂 generate 块嵌套
- 编译指令（`include, `define, `ifdef 等）
- 层次路径引用
- 断言（assert, cover, property）
- 随机化（rand, randc）
- 事务级建模（TLM）

---

### 2. 时钟和复位

#### ✅ 支持（SUPPORTED）

- 单时钟域设计
- 基于名称启发式识别：
  - 时钟：clk, clock, ck
  - 复位：rst, reset
- 从 always 块敏感列表推断边沿：
  - 时钟：posedge clk, negedge clk
  - 复位：posedge rst, negedge rst
- 异步复位推断（异步信号在敏感列表中）
- 同步复位推断（复位信号不在敏感列表中）
- 低电平有效推断（_n, _b, _l, _neg, _bar 后缀）

#### ⚠️ 部分支持（PARTIAL）

- 复位同步逻辑（可识别代码，不推断行为）

#### ❌ 不支持（UNSUPPORTED）

- 多时钟域交互
- 门控时钟
- 复位同步桥分析
- 时钟使能（clock enable）
- 异步复位释放（recovery/removal 分析）

---

### 3. 模块结构

#### ✅ 支持（SUPPORTED）

- 单顶层模块
- 简单层级（顶层直接实例化子模块）
- 参数化实例化
- 端口连接（按位置和按名称）
- 基本实例识别

#### ⚠️ 部分支持（PARTIAL）

- 层级构建（可识别直接实例，不递归构建完整树）

#### ❌ 不支持（UNSUPPORTED）

- 复杂层级（多层实例、generate 实例）
- 跨文件模块引用
- 库文件（library）引用
- 配置（config）块

---

### 4. 接口和数据流

#### ✅ 支持（SUPPORTED）

- 端口提取（名称、方向、位宽）
- 参数提取（名称、默认值）
- 基本数据流识别（从端口到 always 块）

#### ⚠️ 部分支持（PARTIAL）

- 简单协议推断（基于信号命名和端口组）

#### ❌ 不支持（UNSUPPORTED）

- 复杂协议推断（AXI, AXI-Stream, APB 等）
- 握手信号分析（valid/ready 交互）
- 时序约束推断
- 流水线分析

---

### 5. 仿真日志分析

#### ✅ 支持（SUPPORTED）

- ModelSim 风格日志
- 错误提取（** Error:）
- 警告提取（** Warning:）
- 断言失败提取
- 测试结果标记（TEST PASSED, TEST FAILED）
- 错误计数解析
- 时间信息提取

#### ⚠️ 部分支持（PARTIAL）

- 其他仿真器日志（有限支持，依赖格式相似性）

#### ❌ 不支持（UNSUPPORTED）

- 波形数据库（VCD, FSDB, WLF）
- 时序报告解析
- 覆盖率报告解析
- 功耗报告解析

---

### 6. 失败分析

#### ✅ 支持（SUPPORTED）

- 按时间排序失败事件
- 首个失败定位
- 失败类型分类（assertion, error, mismatch）
- 失败消息提取

#### ❌ 不支持（UNSUPPORTED）

- 波形级失败定位
- 根因分析
- 失败影响范围分析

---

## 行为推断限制

### ✅ 可自动推断

- 基本组合逻辑（从 always @* 块推断）
- 基本时序逻辑（从 always @(posedge clk) 推断）
- 复位行为（从 reset 条件推断）
- 简单计数器（从 +1 操作推断）

### ⚠️ 需要用户补充

- 协议时序要求
- 握手行为
- 状态机转换意图
- 性能要求（延迟、吞吐）
- 边界条件行为

### ❌ 无法自动推断

- 设计意图和高层语义
- 业务逻辑正确性
- 未在 RTL 中体现的约束
- 隐式假设（如时钟频率、复位序列）

---

## 端到端流程支持

### ✅ 完整支持

1. RTL 结构提取 → 结构化分析结果
2. 仿真日志解析 → PASS/FAIL 判定
3. 失败提取 → 首个失败定位

### ⚠️ 部分支持

1. RTL 分析整合（需工具输出整合）
2. 行为规格读取（需手动创建）

### ❌ 暂不支持

1. Testbench 自动生成
2. 仿真器自动集成
3. 验证报告自动生成

---

## 典型支持案例

### 案例 1：简单计数器

**文件**：`fixtures/rtl/normal/counter.v`

**支持特性**：
- ✅ 模块识别
- ✅ 端口提取（clk, rst_n, enable, count）
- ✅ 参数提取（WIDTH）
- ✅ 时钟识别（clk, posedge）
- ✅ 复位识别（rst_n, negedge, async, active low）
- ✅ 基本行为推断（复位清零，enable 时计数）

**不支持**：
- ❌ 计数溢出行为（需用户补充）
- ❌ enable 时序要求（需用户补充）

---

### 案例 2：错误计数器

**文件**：`fixtures/rtl/normal/counter_buggy.v`

**支持特性**：
- ✅ 所有正常计数器支持特性
- ✅ RTL 结构分析（与正常版本相同）

**验证能力**：
- ✅ 如果有自检 testbench，可以检测到 +2 错误
- ⚠️ 需要 testbench 明确期望行为

---

## 阻断条件

以下情况会阻断端到端流程：

1. ❌ RTL 文件不存在或无法读取
2. ❌ 无法识别顶层模块
3. ❌ 无法识别时钟或复位信号
4. ❌ 包含不支持的 SystemVerilog 特性
5. ❌ 仿真器不可用且用户未提供命令
6. ❌ 仿真日志格式不支持
7. ❌ 日志证据冲突（如同时存在 assertion failure 和零错误计数）

---

## 验证方法

### 单元测试
- 每个 RTL 工具在 counter.v 上验证
- 每个仿真工具在 sim_pass.log 和 sim_fail.log 上验证

### 端到端测试
- RTL 提取 → 分析整合 → Schema 验证
- 日志解析 → PASS/FAIL 判定 → 证据冲突检测
- 失败提取 → 首个失败定位

### 不支持的验证
- ❌ 真实仿真执行（需要仿真器集成）
- ❌ Testbench 编译和运行（需要 testbench 生成）
- ❌ 波形分析（需要波形工具）

---

## 下一步扩展

### Milestone 3 预计扩展
1. Testbench 生成工具
2. 仿真器集成脚本
3. 验证报告生成
4. 更多 Fixture（AXI, FIFO, FSM）

### 不在当前计划内
1. 完整 CDC 分析
2. 完整时序分析
3. 波形查看器集成
4. 覆盖率驱动验证

---

## 版本历史

- v1.0: 2026-08-04, 初始支持范围定义，基于 counter.v fixture