from typing import Any

from runtime.core import Runtime
from runtime.errors import ContractError


class OmpPiAdapter:
    """Thin platform-neutral prototype adapter; Runtime remains the authority."""

    def __init__(self, runtime, role_layer=None):
        self.runtime = runtime
        self.role_layer = role_layer

    def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("kind") == "command":
            return {"kind": "command_result", "result": self.runtime.dispatch(request.get("command", {}))}
        if request.get("kind") == "role":
            if self.role_layer is None:
                raise ContractError("ROLE_LAYER_UNAVAILABLE", "No Role Invocation Layer configured")
            return {"kind": "role_result", "result": self.role_layer.invoke(request.get("request", {}))}
        if request.get("kind") == "restore":
            self.runtime = Runtime.restore(self.runtime.event_store)
            return {"kind": "restore_result", "result": {"last_sequence": self.runtime.event_store.last_sequence()}}
        raise ContractError("ADAPTER_REQUEST_INVALID", "kind must be command or role")
