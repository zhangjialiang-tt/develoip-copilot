#!/usr/bin/env python3
"""Protocol adapter registry and base classes for universal simulation framework."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import json
from pathlib import Path


class ProtocolAdapter(ABC):
    """Base class for protocol adapters."""

    @abstractmethod
    def can_handle(self, analysis_result: Dict) -> bool:
        """Check if this adapter can handle the given RTL analysis result."""
        pass

    @abstractmethod
    def extract_semantics(self, analysis_result: Dict) -> Dict:
        """Extract interface semantics from analysis result."""
        pass

    @abstractmethod
    def generate_checker(self, semantics: Dict) -> str:
        """Generate protocol checker code."""
        pass

    @abstractmethod
    def get_stimulus_templates(self) -> List[Dict]:
        """Get stimulus templates for this protocol."""
        pass

    def get_protocol_name(self) -> str:
        """Return protocol name."""
        return self.__class__.__name__.replace("Adapter", "").lower()


class SimplePortAdapter(ProtocolAdapter):
    """Adapter for simple port-based modules (no complex protocol)."""

    def can_handle(self, analysis_result: Dict) -> bool:
        """Simple ports can always handle (fallback adapter)."""
        return True

    def extract_semantics(self, analysis_result: Dict) -> Dict:
        """Extract simple port semantics."""
        semantics = {
            "protocol_type": "simple",
            "ports": [],
            "clocks": analysis_result.get("clocks", []),
            "resets": analysis_result.get("resets", [])
        }

        for port in analysis_result.get("ports", []):
            semantics["ports"].append(self._infer_port_semantics(port))

        return semantics

    def _infer_port_semantics(self, port: Dict) -> Dict:
        """Infer semantics for a single port."""
        name = port["name"].lower()
        direction = port["direction"]
        width = port.get("width_expression")

        # Clock signals
        if any(kw in name for kw in ["clk", "clock"]):
            return {
                "name": port["name"],
                "type": "clock",
                "direction": direction,
                "width": width
            }

        # Reset signals
        if any(kw in name for kw in ["rst", "reset"]):
            active_level = "low" if name.endswith("_n") else "high"
            return {
                "name": port["name"],
                "type": "reset",
                "direction": direction,
                "active_level": active_level,
                "width": width
            }

        # Enable/control signals
        if any(kw in name for kw in ["enable", "en", "start"]):
            return {
                "name": port["name"],
                "type": "control",
                "subtype": "enable",
                "direction": direction,
                "width": width
            }

        # Data signals
        if any(kw in name for kw in ["data", "d_", "din", "dout", "in", "out"]):
            return {
                "name": port["name"],
                "type": "data",
                "direction": direction,
                "width": width
            }

        # Valid/ready handshaking
        if name in ["valid", "ready"]:
            return {
                "name": port["name"],
                "type": "handshake",
                "subtype": name,
                "direction": direction,
                "width": width
            }

        # Default: unknown
        return {
            "name": port["name"],
            "type": "unknown",
            "direction": direction,
            "width": width,
            "confidence": "low"
        }

    def generate_checker(self, semantics: Dict) -> str:
        """Generate simple checker code."""
        # For simple protocols, checker is minimal
        return """
  // Basic checker for simple protocol
  always @(posedge clk) begin
    if (!rst_n) begin
      // Reset state
    end else begin
      // Add custom checks based on design requirements
    end
  end
"""

    def get_stimulus_templates(self) -> List[Dict]:
        """Get simple stimulus templates."""
        return [
            {
                "name": "basic_operation",
                "description": "Basic operation test",
                "steps": [
                    "reset_sequence();",
                    "wait_cycles(10);",
                    "apply_stimulus();",
                    "wait_cycles(10);",
                    "check_results();"
                ]
            },
            {
                "name": "enable_toggle",
                "description": "Toggle enable signal",
                "steps": [
                    "reset_sequence();",
                    "force_enable(0);",
                    "wait_cycles(5);",
                    "force_enable(1);",
                    "wait_cycles(10);",
                    "force_enable(0);",
                    "wait_cycles(5);"
                ]
            }
        ]


class AXILiteAdapter(ProtocolAdapter):
    """Adapter for AXI4-Lite protocol."""

    AXI_LITE_SIGNALS = {
        "write_address": ["s_axi_awaddr", "s_axi_awvalid", "s_axi_awready"],
        "write_data": ["s_axi_wdata", "s_axi_wstrb", "s_axi_wvalid", "s_axi_wready"],
        "write_response": ["s_axi_bresp", "s_axi_bvalid", "s_axi_bready"],
        "read_address": ["s_axi_araddr", "s_axi_arvalid", "s_axi_arready"],
        "read_data": ["s_axi_rdata", "s_axi_rresp", "s_axi_rvalid", "s_axi_rready"]
    }

    def can_handle(self, analysis_result: Dict) -> bool:
        """Check if RTL has AXI-Lite interface."""
        ports = {p["name"] for p in analysis_result.get("ports", [])}

        # Check for minimum AXI-Lite signals
        required_signals = ["s_axi_awaddr", "s_axi_wdata", "s_axi_araddr"]
        return all(sig in ports for sig in required_signals)

    def extract_semantics(self, analysis_result: Dict) -> Dict:
        """Extract AXI-Lite interface semantics."""
        ports = {p["name"]: p for p in analysis_result.get("ports", [])}

        semantics = {
            "protocol_type": "axi_lite",
            "version": "1.0",
            "interfaces": {
                "write_address": self._extract_channel(ports, self.AXI_LITE_SIGNALS["write_address"]),
                "write_data": self._extract_channel(ports, self.AXI_LITE_SIGNALS["write_data"]),
                "write_response": self._extract_channel(ports, self.AXI_LITE_SIGNALS["write_response"]),
                "read_address": self._extract_channel(ports, self.AXI_LITE_SIGNALS["read_address"]),
                "read_data": self._extract_channel(ports, self.AXI_LITE_SIGNALS["read_data"])
            },
            "timing": {
                "setup_time_ns": 1.0,
                "hold_time_ns": 1.0,
                "max_wait_cycles": 100
            }
        }

        return semantics

    def _extract_channel(self, ports: Dict, signal_names: List[str]) -> Dict:
        """Extract channel information."""
        channel = {"signals": []}

        for sig_name in signal_names:
            if sig_name in ports:
                port = ports[sig_name]
                channel["signals"].append({
                    "name": sig_name,
                    "direction": port["direction"],
                    "width": port.get("width_expression")
                })

        return channel

    def generate_checker(self, semantics: Dict) -> str:
        """Generate AXI-Lite protocol checker."""
        return """
  // AXI-Lite protocol checker
  // Write address channel
  property aw_valid_ready;
    @(posedge clk) disable iff (!rst_n)
    (s_axi_awvalid) |-> ##[0:100] s_axi_awready;
  endproperty
  assert_aw_valid_ready: assert property(aw_valid_ready);

  // Write data channel
  property w_valid_ready;
    @(posedge clk) disable iff (!rst_n)
    (s_axi_wvalid) |-> ##[0:100] s_axi_wready;
  endproperty
  assert_w_valid_ready: assert property(w_valid_ready);

  // Read address channel
  property ar_valid_ready;
    @(posedge clk) disable iff (!rst_n)
    (s_axi_arvalid) |-> ##[0:100] s_axi_arready;
  endproperty
  assert_ar_valid_ready: assert property(ar_valid_ready);

  // Read data channel
  property r_valid_ready;
    @(posedge clk) disable iff (!rst_n)
    (s_axi_rvalid) |-> ##[0:100] s_axi_rready;
  endproperty
  assert_r_valid_ready: assert property(r_valid_ready);

  // Response should be OKAY (0)
  property bresp_okay;
    @(posedge clk) disable iff (!rst_n)
    (s_axi_bvalid) |-> (s_axi_bresp == 2'b00);
  endproperty
  assert_bresp_okay: assert property(bresp_okay);

  property rresp_okay;
    @(posedge clk) disable iff (!rst_n)
    (s_axi_rvalid) |-> (s_axi_rresp == 2'b00);
  endproperty
  assert_rresp_okay: assert property(rresp_okay);
"""

    def get_stimulus_templates(self) -> List[Dict]:
        """Get AXI-Lite stimulus templates."""
        return [
            {
                "name": "axi_lite_write_read",
                "description": "Basic AXI-Lite write and read",
                "steps": [
                    "reset_sequence();",
                    "axi_write(32'h0000_0000, 32'hDEAD_BEEF);",
                    "axi_read(32'h0000_0000, 32'hDEAD_BEEF);",
                    "axi_write(32'h0000_0004, 32'h1234_5678);",
                    "axi_read(32'h0000_0004, 32'h1234_5678);"
                ]
            },
            {
                "name": "axi_lite_burst",
                "description": "Burst write and read",
                "steps": [
                    "reset_sequence();",
                    "for (int i = 0; i < 16; i++) begin",
                    "  axi_write(32'h0000_0000 + i*4, i);",
                    "end",
                    "for (int i = 0; i < 16; i++) begin",
                    "  axi_read(32'h0000_0000 + i*4, i);",
                    "end"
                ]
            }
        ]


class ProtocolAdapterRegistry:
    """Registry for protocol adapters."""

    def __init__(self):
        self.adapters: List[ProtocolAdapter] = []

        # Register built-in adapters
        self.register_adapter(AXILiteAdapter())
        self.register_adapter(SimplePortAdapter())  # Fallback, should be last

    def register_adapter(self, adapter: ProtocolAdapter):
        """Register a protocol adapter."""
        self.adapters.append(adapter)

    def detect_protocol(self, analysis_result: Dict) -> Optional[ProtocolAdapter]:
        """Detect the appropriate protocol adapter."""
        for adapter in self.adapters:
            if adapter.can_handle(analysis_result):
                return adapter

        return None

    def get_adapter(self, protocol_name: str) -> Optional[ProtocolAdapter]:
        """Get adapter by protocol name."""
        for adapter in self.adapters:
            if adapter.get_protocol_name() == protocol_name:
                return adapter

        return None

    def list_protocols(self) -> List[str]:
        """List all registered protocols."""
        return [adapter.get_protocol_name() for adapter in self.adapters]


# Singleton instance
registry = ProtocolAdapterRegistry()


def detect_protocol(analysis_result: Dict) -> Optional[ProtocolAdapter]:
    """Detect protocol from analysis result."""
    adapter = registry.detect_protocol(analysis_result)

    if adapter is None:
        return None

    return adapter


def extract_semantics(analysis_result: Dict, protocol_name: Optional[str] = None) -> Dict:
    """Extract interface semantics."""
    if protocol_name:
        adapter = registry.get_adapter(protocol_name)
    else:
        adapter = detect_protocol(analysis_result)

    if adapter is None:
        raise ValueError(f"No suitable adapter found for RTL")

    return adapter.extract_semantics(analysis_result)


if __name__ == "__main__":
    # Test protocol detection
    import sys

    if len(sys.argv) < 2:
        print("Usage: python protocol_adapter.py <analysis.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        analysis = json.load(f)

    adapter = detect_protocol(analysis)

    if adapter:
        print(f"Detected protocol: {adapter.get_protocol_name()}")
        semantics = adapter.extract_semantics(analysis)
        print(json.dumps(semantics, indent=2))
    else:
        print("No suitable protocol adapter found")