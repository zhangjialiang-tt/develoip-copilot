import json

import pytest

from runtime.omp_protocol import PROTOCOL_VERSION, ProtocolError, error_frame, parse_request, response_frame


def test_parse_request_accepts_valid_frame():
    request = parse_request(json.dumps({"id": "r1", "op": "hello", "params": {}}))
    assert request == {"id": "r1", "op": "hello", "params": {}}


def test_parse_request_defaults_params():
    request = parse_request(json.dumps({"id": "r1", "op": "health"}))
    assert request["params"] == {}


@pytest.mark.parametrize("line,code", [
    ("not json", "BRIDGE_JSON_INVALID"),
    (json.dumps({"op": "hello"}), "BRIDGE_ID_MISSING"),
    (json.dumps({"id": "", "op": "hello"}), "BRIDGE_ID_MISSING"),
    (json.dumps({"id": "r1", "op": "nope"}), "BRIDGE_OP_UNKNOWN"),
    (json.dumps({"id": "r1", "op": "hello", "params": []}), "BRIDGE_PARAMS_INVALID"),
    (json.dumps([1, 2]), "BRIDGE_FRAME_INVALID"),
])
def test_parse_request_rejects_malformed_frames(line, code):
    with pytest.raises(ProtocolError) as error:
        parse_request(line)
    assert error.value.code == code


def test_frames_roundtrip_through_json():
    ok = json.loads(response_frame("r1", {"value": 1}))
    assert ok == {"id": "r1", "ok": True, "result": {"value": 1}}
    err = json.loads(error_frame("r2", "CODE", "message", {"k": "v"}))
    assert err["ok"] is False
    assert err["error"] == {"code": "CODE", "message": "message", "details": {"k": "v"}}


def test_protocol_version_is_stable():
    assert PROTOCOL_VERSION == 1
