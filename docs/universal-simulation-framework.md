# develoip-copilot 通用仿真框架设计

> 版本：v1.0
> 日期：2026-08-04
> 目标：设计能够适配不同 RTL 模块的稳定仿真框架

---

## 1. 设计原则

### 1.1 分层解耦

```
RTL 输入
  ↓
[RTL 分析层] - 统一的接口分析
  ↓
[协议适配层] - 插件化的协议支持
  ↓
[测试生成层] - 场景化的测试生成
  ↓
[仿真执行层] - 仿真器适配
  ↓
[结果分析层] - 统一的结果解析
```

### 1.2 配置驱动

所有非代码信息通过 JSON 配置：
- 接口定义（port definitions）
- 协议描述（protocol descriptions）
- 测试场景（test scenarios）
- 仿真参数（simulation parameters）

### 1.3 渐进增强

- **M1**: 简单端口 + 基础 stimulus
- **M2**: 常见协议（AXI-Lite, APB, UART）
- **M3**: 复杂协议（AXI, AXI-Stream）
- **M4**: 多时钟域 + CDC

### 1.4 向后兼容

- 新框架兼容现有 counter.v
- 现有工具无需修改
- 渐进式迁移

---

## 2. 分层设计

### 2.1 RTL 分析层（已有）

**输入**：RTL 文件
**输出**：统一的 JSON 结构（已有 schema）

**职责**：
- 提取模块接口
- 识别时钟复位
- 标记不确定字段
- 生成 `analysis.json`

**现有工具**：
- `tools/rtl/integrate_analysis.py`
- `schemas/rtl-analysis.schema.json`

---

### 2.2 协议适配层（新增）

**输入**：
- RTL 分析结果（`analysis.json`）
- 协议配置（`protocol.json`）
- 用户补充信息

**输出**：
- 接口语义描述（`interface_semantics.json`）
- 协议行为模型（`protocol_behavior.json`）

**职责**：
- 识别常见协议模式
- 推断接口语义
- 生成协议检查器模板

**插件接口**：

```python
class ProtocolAdapter:
    """协议适配器基类"""

    def can_handle(self, analysis_result) -> bool:
        """判断是否能处理该 RTL"""
        pass

    def extract_semantics(self, analysis_result) -> dict:
        """提取接口语义"""
        pass

    def generate_checker(self, semantics) -> str:
        """生成协议检查器代码"""
        pass

    def get_stimulus_templates(self) -> list[dict]:
        """获取 stimulus 模板"""
        pass
```

**内置适配器**：

1. **SimplePortAdapter**: 简单端口（ready/enable, valid/data）
2. **AXILiteAdapter**: AXI4-Lite 接口
3. **APBAdapter**: APB 接口
4. **UARTAdapter**: UART 接口
5. **CustomAdapter**: 自定义协议（用户配置）

---

### 2.3 测试生成层（新增）

**输入**：
- 接口语义（`interface_semantics.json`）
- 协议行为模型（`protocol_behavior.json`）
- 测试场景配置（`test_scenarios.json`）

**输出**：
- Testbench 代码（`tb_*.sv`）
- 测试向量（`vectors/*.yaml`）
- 运行脚本（`run_sim.sh`）

**职责**：
- 生成 testbench 骨架
- 生成 stimulus 驱动
- 生成 checker/scoreboard
- 生成运行脚本

**关键组件**：

```python
class TestbenchGenerator:
    """Testbench 生成器"""

    def generate_top(self, analysis, semantics) -> str:
        """生成顶层 testbench"""
        pass

    def generate_clock_generator(self, clocks) -> str:
        """生成时钟生成器"""
        pass

    def generate_reset_sequence(self, resets) -> str:
        """生成复位序列"""
        pass

    def generate_stimulus_driver(self, semantics, scenario) -> str:
        """生成 stimulus 驱动"""
        pass

    def generate_checker(self, semantics) -> str:
        """生成 checker"""
        pass

    def generate_scoreboard(self, semantics) -> str:
        """生成 scoreboard"""
        pass
```

---

### 2.4 仿真执行层（增强现有）

**输入**：
- Testbench 文件
- DUT 文件
- 仿真配置（`sim_config.json`）

**输出**：
- 仿真日志（`simulation.log`）
- 波形文件（可选）
- 退出码

**职责**：
- 检测仿真器可用性
- 编译设计
- 运行仿真
- 捕获输出

**仿真器适配器**：

```python
class SimulatorAdapter:
    """仿真器适配器基类"""

    def is_available(self) -> bool:
        """检查仿真器是否可用"""
        pass

    def compile_design(self, files, options) -> subprocess.CompletedProcess:
        """编译设计"""
        pass

    def run_simulation(self, testbench, options) -> subprocess.CompletedProcess:
        """运行仿真"""
        pass

    def get_log_parser(self) -> LogParser:
        """获取日志解析器"""
        pass
```

**内置适配器**：

1. **IverilogAdapter**: iverilog + vvp
2. **ModelSimAdapter**: ModelSim/Questa
3. **VCSAdapter**: Synopsys VCS
4. **XceliumAdapter**: Cadence Xcelium

---

### 2.5 结果分析层（已有）

**输入**：仿真日志
**输出**：结构化结果

**现有工具**：
- `tools/simulation/parse_log.py`
- `tools/simulation/extract_failures.py`

---

## 3. 配置文件设计

### 3.1 协议配置（`protocol.json`）

```json
{
  "protocol_type": "axi_lite",
  "version": "1.0",
  "interfaces": [
    {
      "name": "s_axi",
      "type": "master",
      "signals": [
        {"name": "s_axi_awaddr", "direction": "input", "width": 12},
        {"name": "s_axi_awvalid", "direction": "input"},
        {"name": "s_axi_awready", "direction": "output"},
        {"name": "s_axi_wdata", "direction": "input", "width": 32},
        {"name": "s_axi_wstrb", "direction": "input", "width": 4},
        {"name": "s_axi_wvalid", "direction": "input"},
        {"name": "s_axi_wready", "direction": "output"},
        {"name": "s_axi_bresp", "direction": "output", "width": 2},
        {"name": "s_axi_bvalid", "direction": "output"},
        {"name": "s_axi_bready", "direction": "input"},
        {"name": "s_axi_araddr", "direction": "input", "width": 12},
        {"name": "s_axi_arvalid", "direction": "input"},
        {"name": "s_axi_arready", "direction": "output"},
        {"name": "s_axi_rdata", "direction": "output", "width": 32},
        {"name": "s_axi_rresp", "direction": "output", "width": 2},
        {"name": "s_axi_rvalid", "direction": "output"},
        {"name": "s_axi_rready", "direction": "input"}
      ]
    }
  ],
  "timing": {
    "setup_time_ns": 1.0,
    "hold_time_ns": 1.0,
    "max_wait_cycles": 100
  },
  "behavior": {
    "write_transaction": "axi_lite_write_sequence",
    "read_transaction": "axi_lite_read_sequence"
  }
}
```

---

### 3.2 测试场景配置（`test_scenarios.json`）

```json
{
  "scenarios": [
    {
      "name": "basic_read_write",
      "description": "Basic read/write operations",
      "steps": [
        {"type": "reset", "duration_cycles": 5},
        {"type": "write", "address": "0x000", "data": "0x12345678"},
        {"type": "read", "address": "0x000", "expected_data": "0x12345678"},
        {"type": "write", "address": "0x004", "data": "0xDEADBEEF"},
        {"type": "read", "address": "0x004", "expected_data": "0xDEADBEEF"}
      ]
    },
    {
      "name": "boundary_test",
      "description": "Boundary address testing",
      "steps": [
        {"type": "reset", "duration_cycles": 5},
        {"type": "write", "address": "0x000", "data": "0xFFFFFFFF"},
        {"type": "write", "address": "0xFFC", "data": "0x00000000"},
        {"type": "read", "address": "0x000", "expected_data": "0xFFFFFFFF"},
        {"type": "read", "address": "0xFFC", "expected_data": "0x00000000"}
      ]
    },
    {
      "name": "random_access",
      "description": "Random access pattern",
      "generator": "random_access",
      "parameters": {
        "num_transactions": 100,
        "address_range": [0, 4095],
        "data_range": [0, 0xFFFFFFFF]
      }
    }
  ]
}
```

---

### 3.3 仿真配置（`sim_config.json`）

```json
{
  "simulator": "auto",
  "compile_options": {
    "iverilog": ["-g2012"],
    "modelsim": ["-sv"]
  },
  "run_options": {
    "timeout": 1000,
    "waveform": false,
    "coverage": false
  },
  "output": {
    "log_file": "simulation.log",
    "wave_file": "dump.vcd",
    "coverage_dir": "coverage"
  }
}
```

---

## 4. 工作流程

### 4.1 完整流程

```
1. RTL 分析
   tools/rtl/integrate_analysis.py dut.v --output analysis.json

2. 协议识别
   tools/protocol/detect_protocol.py analysis.json
   → 输出: protocol_type

3. 生成接口语义
   tools/protocol/extract_semantics.py analysis.json --protocol axi_lite
   → 输出: interface_semantics.json

4. 生成测试场景
   tools/testgen/generate_scenarios.py interface_semantics.json
   → 输出: test_scenarios.json

5. 生成 Testbench
   tools/testgen/generate_testbench.py analysis.json interface_semantics.json test_scenarios.json
   → 输出: tb_dut.sv, vectors/

6. 运行仿真
   tools/simulation/run_simulation.py tb_dut.sv dut.v --config sim_config.json
   → 输出: simulation.log

7. 解析结果
   tools/simulation/parse_log.py simulation.log --json
   → 输出: result.json

8. 生成报告
   tools/report/generate_report.py analysis.json result.json
   → 输出: verification_report.md
```

---

### 4.2 简化流程（Milestone 3）

对于简单模块（如 counter.v），可跳过协议识别：

```
RTL 分析 → 用户补充行为规格 → 生成 Testbench → 仿真 → 报告
```

---

## 5. 渐进实施路线

### Milestone 3.1: 简单模块支持

**目标**：支持 counter.v 等简单模块

**实现**：
1. ✅ RTL 分析（已有）
2. ✅ 简单 testbench 生成
3. ✅ iverilog 集成
4. ✅ 基础报告生成

**验收**：
- counter.v → testbench → 仿真 PASS
- counter_buggy.v → testbench → 仿真 FAIL

---

### Milestone 3.2: 常见协议支持

**目标**：支持 AXI-Lite, APB, UART

**实现**：
1. 实现 `AXILiteAdapter`
2. 实现 `APBAdapter`
3. 实现 `UARTAdapter`
4. 协议检查器生成

**验收**：
- AXI-Lite Slave 模块 → testbench → 仿真 PASS
- APB Slave 模块 → testbench → 仿真 PASS

---

### Milestone 3.3: 测试场景生成

**目标**：自动生成多样化测试场景

**实现**：
1. 基础场景模板
2. 边界测试生成
3. 随机测试生成
4. 压力测试生成

**验收**：
- 自动生成 10+ 测试场景
- 覆盖率 > 80%

---

### Milestone 3.4: 高级功能

**目标**：多仿真器、波形、覆盖率

**实现**：
1. ModelSim 适配器
2. 波形生成
3. 覆盖率收集
4. 回归测试框架

**验收**：
- 支持至少 2 种仿真器
- 支持波形分析
- 支持覆盖率报告

---

## 6. 关键技术点

### 6.1 协议识别启发式

```python
def detect_protocol(analysis: dict) -> str:
    """基于端口模式识别协议"""
    ports = {p["name"]: p for p in analysis["ports"]}

    # AXI-Lite 模式
    if all(sig in ports for sig in ["s_axi_awaddr", "s_axi_wdata", "s_axi_araddr"]):
        return "axi_lite"

    # APB 模式
    if all(sig in ports for sig in ["paddr", "pwdata", "prdata"]):
        return "apb"

    # UART 模式
    if all(sig in ports for sig in ["rx", "tx", "baudrate"]):
        return "uart"

    # 默认：简单端口
    return "simple"
```

---

### 6.2 接口语义推断

```python
def infer_port_semantics(port: dict, context: dict) -> dict:
    """推断端口语义"""
    name = port["name"].lower()

    # 时钟信号
    if "clk" in name or "clock" in name:
        return {"type": "clock", "domain": "default"}

    # 复位信号
    if "rst" in name or "reset" in name:
        active_level = "low" if name.endswith("_n") else "high"
        return {"type": "reset", "active_level": active_level}

    # 使能信号
    if "enable" in name or "en" in name:
        return {"type": "control", "subtype": "enable"}

    # 数据信号
    if "data" in name or "d" in name:
        return {"type": "data", "direction": port["direction"]}

    # 默认：未知
    return {"type": "unknown", "confidence": "low"}
```

---

### 6.3 Testbench 模板引擎

使用 Jinja2 模板引擎：

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates/"))

def generate_testbench(template_name: str, context: dict) -> str:
    """从模板生成 testbench"""
    template = env.get_template(template_name)
    return template.render(**context)
```

模板示例（`tb_top.sv.jinja2`）：

```systemverilog
module tb_{{ top_module }}();

  // Clock generation
  {% for clock in clocks %}
  logic {{ clock.name }};
  initial begin
    {{ clock.name }} = 0;
    forever #({{ clock.period_ns }}/2) {{ clock.name }} = ~{{ clock.name }};
  end
  {% endfor %}

  // Reset generation
  {% for reset in resets %}
  logic {{ reset.name }};
  initial begin
    {{ reset.name }} = {{ reset.active_level == 'LOW' ? 1 : 0 }};
    #{{ reset.assertion_cycles }};
    {{ reset.name }} = {{ reset.active_level == 'LOW' ? 0 : 1 }};
  end
  {% endfor %}

  // DUT instantiation
  {{ top_module }} #(
    {% for param in parameters %}
    .{{ param.name }}({{ param.default }}){% if not loop.last %},{% endif %}
    {% endfor %}
  ) dut (
    {% for port in ports %}
    .{{ port.name }}({{ port.name }}){% if not loop.last %},{% endif %}
    {% endfor %}
  );

  // Test scenarios
  initial begin
    {% for scenario in scenarios %}
    // {{ scenario.description }}
    {% for step in scenario.steps %}
    {{ step }};
    {% endfor %}
    {% endfor %}

    $display("All tests passed!");
    $finish;
  end

endmodule
```

---

### 6.4 仿真器自动检测

```python
def detect_simulator() -> str:
    """检测可用的仿真器"""
    simulators = {
        "iverilog": check_command("iverilog"),
        "vsim": check_command("vsim"),
        "vcs": check_command("vcs"),
        "xrun": check_command("xrun")
    }

    available = [name for name, available in simulators.items() if available]

    if not available:
        raise RuntimeError("No simulator found")

    # 优先级：iverilog > vsim > vcs > xrun
    priority = ["iverilog", "vsim", "vcs", "xrun"]
    for sim in priority:
        if sim in available:
            return sim

    return available[0]
```

---

## 7. 错误处理和降级

### 7.1 协议识别失败

**降级策略**：
1. 尝试简单端口模式
2. 请求用户补充接口语义
3. 生成最小 testbench（仅时钟复位）

**用户交互**：
```
无法自动识别协议，请补充接口语义：
1. 端口 'data_in' 的类型？[data/control/status]
2. 端口 'valid' 的作用？[handshake/enable/strobe]
...
```

---

### 7.2 Testbench 生成失败

**降级策略**：
1. 使用最简模板
2. 仅包含基础 stimulus
3. 标记为"需要人工完善"

**产物示例**：
```systemverilog
// AUTO-GENERATED: Needs manual review
module tb_dut();
  // Basic structure only
  // TODO: Add stimulus based on design requirements
endmodule
```

---

### 7.3 仿真执行失败

**错误分类**：
1. 编译错误 → 语法问题，报告到用户
2. 运行时错误 → testbench 问题，建议检查
3. 超时 → 可能死锁，建议检查设计

**降级策略**：
1. 尝试降低仿真精度
2. 尝试简化测试场景
3. 生成部分报告

---

## 8. 扩展性设计

### 8.1 自定义协议

用户可以通过以下方式添加自定义协议：

1. **协议配置文件**：
```json
{
  "protocol_type": "custom",
  "interfaces": [...],
  "behavior": {...}
}
```

2. **协议适配器插件**：
```python
class CustomProtocolAdapter(ProtocolAdapter):
    def can_handle(self, analysis):
        # 自定义识别逻辑
        pass

    def extract_semantics(self, analysis):
        # 自定义语义提取
        pass
```

3. **Stimulus 模板**：
```yaml
# templates/stimulus/custom.yaml
steps:
  - type: custom_operation
    parameters: {...}
```

---

### 8.2 自定义检查器

用户可以添加自定义断言和检查器：

1. **SVA 断言**：
```systemverilog
// assertions/custom.sva
property custom_check;
  @(posedge clk)
  disable iff (!rst_n)
  (valid) |-> ##[1:10] ready;
endproperty
assert_custom_check: assert property(custom_check);
```

2. **SystemVerilog checker**：
```systemverilog
// checkers/custom_checker.sv
checker custom_checker(
  input logic clk,
  input logic rst_n,
  input logic valid,
  input logic ready
);
  // 检查逻辑
endchecker
```

---

## 9. 质量保证

### 9.1 测试策略

1. **单元测试**：每个适配器和生成器
2. **集成测试**：完整流程测试
3. **回归测试**：已知 RTL 模块
4. **性能测试**：大型设计

### 9.2 Golden Files

为每个协议维护 golden testbench：
- `fixtures/golden/axi_lite/tb_slave.sv`
- `fixtures/golden/apb/tb_slave.sv`
- `fixtures/golden/uart/tb_uart.sv`

### 9.3 持续集成

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          python -m pytest tests/
          python tests/e2e/test_rtl_to_verification.py
```

---

## 10. 文档和示例

### 10.1 快速开始

```bash
# 简单模块
python tools/framework/generate_testbench.py dut.v --protocol simple
python tools/simulation/run_simulation.py tb_dut.sv dut.v
python tools/simulation/parse_log.py simulation.log

# AXI-Lite 模块
python tools/framework/generate_testbench.py axi_slave.v --protocol axi_lite
python tools/simulation/run_simulation.py tb_axi_slave.sv axi_slave.v
python tools/simulation/parse_log.py simulation.log
```

### 10.2 示例模块

- `fixtures/examples/counter.v` - 简单计数器
- `fixtures/examples/axi_lite_slave.v` - AXI-Lite 从设备
- `fixtures/examples/apb_slave.v` - APB 从设备
- `fixtures/examples/uart_tx.v` - UART 发送器

### 10.3 最佳实践

1. **命名规范**：使用标准信号命名（`clk`, `rst_n`, `valid`, `ready`）
2. **参数化**：使用参数提高可配置性
3. **注释**：添加清晰的接口注释
4. **测试场景**：定义全面的测试场景

---

## 11. 与现有架构的集成

### 11.1 Skill 集成

更新 `rtl-to-testbench` Skill 的 Procedure：

1. 调用 RTL 分析
2. 调用协议识别
3. 生成 testbench
4. 运行仿真
5. 解析结果
6. 生成报告

### 11.2 Agent 集成

- `rtl-analyst`：使用新的 RTL 分析工具
- `verification-engineer`：使用新的 testbench 生成工具
- `simulation-analyst`：使用新的结果解析工具

### 11.3 工具集成

新的工具放在 `tools/framework/`：
- `tools/framework/detect_protocol.py`
- `tools/framework/extract_semantics.py`
- `tools/framework/generate_testbench.py`
- `tools/framework/generate_scenarios.py`

---

## 12. 风险和缓解

### 12.1 风险

1. **协议识别不准确**：误判协议类型
2. **生成的 testbench 质量低**：验证不充分
3. **仿真器兼容性问题**：不同仿真器行为差异
4. **复杂模块支持不足**：多时钟域、异步复位

### 12.2 缓解措施

1. **用户确认机制**：识别结果需用户确认
2. **golden file 对比**：与已知 good testbench 对比
3. **多仿真器测试**：在多个仿真器上验证
4. **渐进支持**：先简单后复杂

---

## 版本
- v1.0: 2026-08-04, 初始框架设计