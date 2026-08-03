"""Newline-delimited JSON protocol between OMP and the Python Runtime Bridge.

The bridge is a protocol translator only: every mutation still enters the
Runtime through ``Runtime.dispatch()``. Frames:

request:      {"id": "<req-id>", "op": "<op>", "params": {...}}
response ok:  {"id": "<req-id>", "ok": true, "result": {...}}
response err: {"id": "<req-id>", "ok": false, "error": {"code","message","details"}}
"""
from __future__ import annotations

import json
from typing import Any

PROTOCOL_VERSION = 1

OPS = (
    "hello",
    "health",
    "status",
    "dispatch",
    "query",
    "restore",
    "save_snapshot",
    "invoke_role_result",
    "submit_candidates",
    "guard_check",
    "workspace_status",
    "capture_baseline",
    "shutdown",
)


class ProtocolError(Exception):
    """A malformed bridge frame; never produces partial Runtime effects."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def parse_request(line: str) -> dict[str, Any]:
    try:
        frame = json.loads(line)
    except json.JSONDecodeError as error:
        raise ProtocolError("BRIDGE_JSON_INVALID", f"Request is not valid JSON: {error}") from error
    if not isinstance(frame, dict):
        raise ProtocolError("BRIDGE_FRAME_INVALID", "Request frame must be a JSON object")
    request_id = frame.get("id")
    if not isinstance(request_id, str) or not request_id:
        raise ProtocolError("BRIDGE_ID_MISSING", "Request frame needs a non-empty string id")
    op = frame.get("op")
    if not isinstance(op, str) or op not in OPS:
        raise ProtocolError("BRIDGE_OP_UNKNOWN", f"Unknown op: {op!r}")
    params = frame.get("params", {})
    if not isinstance(params, dict):
        raise ProtocolError("BRIDGE_PARAMS_INVALID", "params must be an object")
    return {"id": request_id, "op": op, "params": params}


def response_frame(request_id: str | None, result: dict[str, Any]) -> str:
    return json.dumps({"id": request_id, "ok": True, "result": result}, sort_keys=True, ensure_ascii=False)


def error_frame(request_id: str | None, code: str, message: str, details: dict[str, Any] | None = None) -> str:
    return json.dumps(
        {"id": request_id, "ok": False, "error": {"code": code, "message": message, "details": details or {}}},
        sort_keys=True,
        ensure_ascii=False,
    )
