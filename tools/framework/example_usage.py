#!/usr/bin/env python3
"""Example: Using the universal simulation framework for different RTL modules."""
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tools.framework.protocol_adapter import (
    detect_protocol,
    extract_semantics,
    registry
)
from tools.rtl.integrate_analysis import integrate_analysis


def example_counter_module():
    """Example 1: Simple counter module."""
    print("=" * 60)
    print("Example 1: Simple Counter Module")
    print("=" * 60)

    # Step 1: Analyze RTL
    print("\n1. Analyzing RTL...")
    analysis = integrate_analysis(str(REPO_ROOT / "fixtures/rtl/normal/counter.v"))
    print(f"   Top module: {analysis['top_module']}")
    print(f"   Status: {analysis['status']}")

    # Step 2: Detect protocol
    print("\n2. Detecting protocol...")
    adapter = detect_protocol(analysis)
    if adapter:
        print(f"   Detected: {adapter.get_protocol_name()}")
    else:
        print("   No protocol detected")

    # Step 3: Extract semantics
    print("\n3. Extracting semantics...")
    semantics = extract_semantics(analysis)
    print(f"   Protocol type: {semantics['protocol_type']}")
    print(f"   Number of ports: {len(semantics['ports'])}")

    # Print port semantics
    print("\n   Port semantics:")
    for port in semantics['ports'][:4]:  # Show first 4
        print(f"     - {port['name']}: {port['type']} ({port['direction']})")

    # Step 4: Get stimulus templates
    print("\n4. Getting stimulus templates...")
    templates = adapter.get_stimulus_templates()
    print(f"   Available templates: {len(templates)}")
    for tmpl in templates:
        print(f"     - {tmpl['name']}: {tmpl['description']}")

    return analysis, semantics


def example_axi_lite_module():
    """Example 2: AXI-Lite module (hypothetical)."""
    print("\n" + "=" * 60)
    print("Example 2: AXI-Lite Module (Hypothetical)")
    print("=" * 60)

    # Create hypothetical analysis result for AXI-Lite
    analysis = {
        "top_module": "axi_lite_slave",
        "status": "COMPLETE",
        "ports": [
            {"name": "s_axi_aclk", "direction": "input"},
            {"name": "s_axi_aresetn", "direction": "input"},
            {"name": "s_axi_awaddr", "direction": "input", "width_expression": "11:0"},
            {"name": "s_axi_awvalid", "direction": "input"},
            {"name": "s_axi_awready", "direction": "output"},
            {"name": "s_axi_wdata", "direction": "input", "width_expression": "31:0"},
            {"name": "s_axi_wstrb", "direction": "input", "width_expression": "3:0"},
            {"name": "s_axi_wvalid", "direction": "input"},
            {"name": "s_axi_wready", "direction": "output"},
            {"name": "s_axi_bresp", "direction": "output", "width_expression": "1:0"},
            {"name": "s_axi_bvalid", "direction": "output"},
            {"name": "s_axi_bready", "direction": "input"},
            {"name": "s_axi_araddr", "direction": "input", "width_expression": "11:0"},
            {"name": "s_axi_arvalid", "direction": "input"},
            {"name": "s_axi_arready", "direction": "output"},
            {"name": "s_axi_rdata", "direction": "output", "width_expression": "31:0"},
            {"name": "s_axi_rresp", "direction": "output", "width_expression": "1:0"},
            {"name": "s_axi_rvalid", "direction": "output"},
            {"name": "s_axi_rready", "direction": "input"}
        ],
        "clocks": [
            {"name": "s_axi_aclk", "edge": "posedge", "confidence": "HIGH"}
        ],
        "resets": [
            {"name": "s_axi_aresetn", "active_level": "LOW", "kind": "ASYNC", "confidence": "HIGH"}
        ]
    }

    print("\n1. Hypothetical AXI-Lite module analysis")
    print(f"   Top module: {analysis['top_module']}")
    print(f"   Number of ports: {len(analysis['ports'])}")

    # Step 2: Detect protocol
    print("\n2. Detecting protocol...")
    adapter = detect_protocol(analysis)
    if adapter:
        print(f"   Detected: {adapter.get_protocol_name()}")
    else:
        print("   No protocol detected")

    # Step 3: Extract semantics
    print("\n3. Extracting semantics...")
    semantics = extract_semantics(analysis)
    print(f"   Protocol type: {semantics['protocol_type']}")
    print(f"   Number of channels: {len(semantics['interfaces'])}")

    # Print interface channels
    print("\n   Interface channels:")
    for channel_name, channel in semantics['interfaces'].items():
        print(f"     - {channel_name}: {len(channel['signals'])} signals")

    # Step 4: Get checker code
    print("\n4. Generating protocol checker...")
    checker = adapter.generate_checker(semantics)
    print(f"   Checker code length: {len(checker)} characters")
    print("\n   Checker preview (first 300 chars):")
    print("   " + checker[:300].replace("\n", "\n   "))

    # Step 5: Get stimulus templates
    print("\n5. Getting stimulus templates...")
    templates = adapter.get_stimulus_templates()
    print(f"   Available templates: {len(templates)}")
    for tmpl in templates:
        print(f"     - {tmpl['name']}: {tmpl['description']}")
        print(f"       Steps: {len(tmpl['steps'])}")

    return analysis, semantics


def example_custom_protocol():
    """Example 3: Custom protocol with user configuration."""
    print("\n" + "=" * 60)
    print("Example 3: Custom Protocol with User Configuration")
    print("=" * 60)

    # Hypothetical custom interface
    analysis = {
        "top_module": "custom_interface",
        "status": "COMPLETE",
        "ports": [
            {"name": "clk", "direction": "input"},
            {"name": "rst_n", "direction": "input"},
            {"name": "data_in", "direction": "input", "width_expression": "15:0"},
            {"name": "data_out", "direction": "output", "width_expression": "15:0"},
            {"name": "valid_in", "direction": "input"},
            {"name": "valid_out", "direction": "output"},
            {"name": "ready", "direction": "input"}
        ],
        "clocks": [{"name": "clk", "edge": "posedge"}],
        "resets": [{"name": "rst_n", "active_level": "LOW"}]
    }

    print("\n1. Custom interface analysis")
    print(f"   Top module: {analysis['top_module']}")
    print(f"   Number of ports: {len(analysis['ports'])}")

    # Step 2: Detect protocol (will fall back to SimplePortAdapter)
    print("\n2. Detecting protocol...")
    adapter = detect_protocol(analysis)
    if adapter:
        print(f"   Detected: {adapter.get_protocol_name()}")
    else:
        print("   No protocol detected")

    # Step 3: Extract semantics
    print("\n3. Extracting semantics...")
    semantics = extract_semantics(analysis)
    print(f"   Protocol type: {semantics['protocol_type']}")

    # Print port semantics
    print("\n   Port semantics:")
    for port in semantics['ports']:
        print(f"     - {port['name']}: {port['type']}")
        if port['type'] == 'unknown':
            print(f"       ⚠️  Low confidence, may need user specification")

    print("\n4. Recommendation:")
    print("   - Some ports have unknown semantics")
    print("   - Consider creating a custom protocol adapter")
    print("   - Or provide interface semantics via configuration file")

    return analysis, semantics


def example_framework_integration():
    """Example 4: Complete framework integration."""
    print("\n" + "=" * 60)
    print("Example 4: Complete Framework Integration")
    print("=" * 60)

    print("\n1. Available protocols in framework:")
    protocols = registry.list_protocols()
    for protocol in protocols:
        print(f"   - {protocol}")

    print("\n2. Processing counter module through framework:")
    print("   RTL → Analysis → Protocol Detection → Semantics → Testbench Generation")

    # Simulate framework flow
    analysis = integrate_analysis(str(REPO_ROOT / "fixtures/rtl/normal/counter.v"))
    adapter = detect_protocol(analysis)
    semantics = extract_semantics(analysis)
    templates = adapter.get_stimulus_templates()

    print("\n   Framework output:")
    print(f"     - Analysis: {analysis['status']}")
    print(f"     - Protocol: {adapter.get_protocol_name()}")
    print(f"     - Semantics: {len(semantics['ports'])} ports")
    print(f"     - Templates: {len(templates)} scenarios")

    print("\n3. Next steps in framework:")
    print("   - Generate testbench from semantics")
    print("   - Generate stimulus from templates")
    print("   - Compile and run simulation")
    print("   - Parse results and generate report")

    print("\n4. Framework benefits:")
    print("   ✓ Consistent interface across different RTL types")
    print("   ✓ Pluggable protocol adapters")
    print("   ✓ Automatic protocol detection")
    print("   ✓ Configurable stimulus generation")
    print("   ✓ Unified result analysis")


def main():
    """Run all examples."""
    print("Universal Simulation Framework - Usage Examples")
    print("=" * 60)

    try:
        # Example 1: Counter module
        example_counter_module()

        # Example 2: AXI-Lite module
        example_axi_lite_module()

        # Example 3: Custom protocol
        example_custom_protocol()

        # Example 4: Framework integration
        example_framework_integration()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()