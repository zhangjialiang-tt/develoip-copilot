# develoip-copilot

Milestone 2 当前实现：QSPI Vertical Slice Runtime。

## 验证

```powershell
python -m pytest -q
python fixtures/qspi-concat/qspi_fixture.py --baseline A
python fixtures/qspi-concat/qspi_fixture.py --baseline B
```

Runtime 公共入口为 `runtime.core.Runtime.dispatch()`、`query()`、`restore()` 和 `save_snapshot()`。语义权威仍是 [docs/execution-contract.md](docs/execution-contract.md)；实现选择记录在 [docs/milestone2-decisions.md](docs/milestone2-decisions.md)。

本阶段不访问真实板卡，不修改生产工程，不自动提交或推送。
