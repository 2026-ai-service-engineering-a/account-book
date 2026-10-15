from __future__ import annotations

import json

from mcp_server.application.use_cases.tool_payload import MAX_BYTES, fit


def test_trims_the_list_from_the_back_until_it_fits():
    data: dict[str, object] = {"changes": [{"name": "가" * 100, "i": i} for i in range(200)]}
    assert fit(data, "changes") is True
    assert len(json.dumps(data, ensure_ascii=False).encode()) <= MAX_BYTES
    rows = data["changes"]
    assert isinstance(rows, list) and rows[0]["i"] == 0


def test_a_small_payload_is_left_alone():
    data: dict[str, object] = {"changes": [1, 2, 3]}
    assert fit(data, "changes") is False and data["changes"] == [1, 2, 3]
