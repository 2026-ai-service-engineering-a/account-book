from __future__ import annotations

from agent.infrastructure.http.categories_reply import CategoriesReply


def test_the_dictionary():
    body = [{"id": "cafe", "name": "카페", "direction": "expense"}]
    (line,) = CategoriesReply.model_validate(body).lines()
    assert (line.id, line.name) == ("cafe", "카페")
