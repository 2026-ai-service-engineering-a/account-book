from __future__ import annotations

from api.domain.errors import InvalidEmbedding, InvalidTransaction


def test_carries_details_and_is_its_own_error():
    assert InvalidEmbedding({"vector": "차원"}).details == {"vector": "차원"}
    assert not issubclass(InvalidEmbedding, InvalidTransaction)
