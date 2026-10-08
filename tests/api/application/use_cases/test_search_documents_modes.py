from __future__ import annotations

import pytest

from api.application.use_cases import SearchDocuments
from api.application.use_cases.search_documents import FUSION_POOL
from api.domain.errors import InvalidEmbedding
from api.domain.rules.rank_fusion import reciprocal_rank_fusion
from api.domain.values import ChunkStrategy, SearchMode
from tests.api.application.use_cases.test_search_documents import library
from tests.api.conftest import FakeUnitOfWork

MODEL = "m@768"
TARGET = "paragraph:할부거래에 관한 법률/제8조/1"


def unit(i: int) -> tuple[float, ...]:
    return tuple(1.0 if j == i else 0.0 for j in range(768))


def embedded() -> FakeUnitOfWork:
    """조각마다 서로 다른 단위 벡터. 질문 벡터를 TARGET의 것으로 주면 TARGET이 가장 가깝다."""
    uow = library()
    hashes = sorted({c.text_hash for c in uow.documents.chunks.values()})
    for i, h in enumerate(hashes):
        uow.index.put_embedding(MODEL, h, unit(i))
    return uow


def vector_of(uow: FakeUnitOfWork, chunk_id: str) -> tuple[float, ...]:
    return uow.index.vectors[(MODEL, uow.documents.chunks[chunk_id].text_hash)]


def test_vector_finds_the_nearest_meaning_even_without_shared_words():
    uow = embedded()
    search = SearchDocuments(uow)
    hits = search(
        "노트북 취소", ChunkStrategy.PARAGRAPH, 3, SearchMode.VECTOR, vector_of(uow, TARGET), MODEL
    )
    assert hits[0].chunk.id == TARGET and hits[0].score == pytest.approx(1.0)


def test_hybrid_fuses_ranks_and_keeps_k_as_a_prefix():
    uow = embedded()
    search = SearchDocuments(uow)
    vector, words = vector_of(uow, TARGET), "수영장 및 체력단련장"
    eight = search(words, ChunkStrategy.PARAGRAPH, 8, SearchMode.HYBRID, vector, MODEL)
    three = search(words, ChunkStrategy.PARAGRAPH, 3, SearchMode.HYBRID, vector, MODEL)
    assert [h.chunk.id for h in three] == [h.chunk.id for h in eight[:3]]
    # 두 검색의 후보 목록(각 FUSION_POOL개)을 직접 받아 RRF로 합친 순서와 같다
    lexical = uow.documents.search(words, ChunkStrategy.PARAGRAPH, FUSION_POOL)
    semantic = uow.documents.nearest(vector, MODEL, ChunkStrategy.PARAGRAPH, FUSION_POOL)
    expected = reciprocal_rank_fusion(
        [[h.chunk.id for h in lexical], [h.chunk.id for h in semantic]]
    )
    assert [h.chunk.id for h in eight] == [key for key, _ in expected[:8]]
    assert [h.score for h in eight] == pytest.approx([score for _, score in expected[:8]])
    assert all(h.score < 0.04 for h in eight)  # RRF 점수 — 유사도가 아니다


@pytest.mark.parametrize("mode", [SearchMode.VECTOR, SearchMode.HYBRID])
def test_vector_modes_need_a_vector_of_the_right_size(mode):
    search = SearchDocuments(embedded())
    with pytest.raises(InvalidEmbedding):
        search("카드", ChunkStrategy.PARAGRAPH, 5, mode, None, MODEL)
    with pytest.raises(InvalidEmbedding):
        search("카드", ChunkStrategy.PARAGRAPH, 5, mode, (0.1, 0.2), MODEL)


def test_vector_without_any_embedding_for_the_model_finds_nothing():
    uow = embedded()
    hits = SearchDocuments(uow)(
        "카드", ChunkStrategy.PARAGRAPH, 5, SearchMode.VECTOR, unit(0), "other@768"
    )
    assert hits == ()
