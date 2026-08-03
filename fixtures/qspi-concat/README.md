# QSPI Concatenation Fixture

`Baseline A` reproduces a byte-lane concatenation defect. `Baseline B` is the authorized fixed model.

```powershell
python fixtures/qspi-concat/qspi_fixture.py --baseline A
python fixtures/qspi-concat/qspi_fixture.py --baseline B
```

The fixture contains a Verilog reference module, a Python self-checking testbench, fixed input data, expected output, and an independent `int.from_bytes` comparison. It does not access a real board or production workspace.
