from __future__ import annotations

from mcp_server.infrastructure.http.categories_reply import CategoriesReply


def test_keeps_the_id_and_the_name():
    reply = [{"id": "food", "name": "식비", "direction": "expense"}]
    assert CategoriesReply.model_validate(reply).rows() == [{"id": "food", "name": "식비"}]
