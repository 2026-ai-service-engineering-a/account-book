from __future__ import annotations

import asyncio

from agent.application.ports import Embedder, LedgerApi

# 제공자 한 번에 보내는 텍스트 수. Gemini의 묶음 임베딩 상한(100) 안이다.
_BATCH = 100
# 한 번 돌 때의 상한. 쓰기가 조용히 실패해 pending이 줄지 않아도 끝없이 돌지 않게.
_ROUNDS = 20


class SyncIndex:
    """색인 안 된 텍스트를 api에서 당겨 와 임베딩하고 돌려준다(category-suggestion-rag 4.3).

    화살표는 agent → api 한 방향이다. api는 agent를 부르지 않으니 agent가 당긴다. 분류 요청이
    올 때마다 먼저 한 번 돈다 — 방금 저장한 거래가 바로 다음 검색의 이웃이 된다.
    """

    def __init__(self, ledger: LedgerApi, embedder: Embedder) -> None:
        self._ledger = ledger
        self._embedder = embedder
        # 요청 둘이 동시에 와도 같은 텍스트를 두 번 임베딩하지 않게
        self._lock = asyncio.Lock()

    async def run(self) -> int:
        """임베딩한 텍스트 수. 이미 다 색인돼 있으면 0이고, 제공자는 부르지 않는다."""
        model = self._embedder.model
        done = 0
        async with self._lock:
            for _ in range(_ROUNDS):
                pending = await self._ledger.pending(model, _BATCH)
                if not pending:
                    break
                vectors = await self._embedder.embed([p.text for p in pending])
                for item, vector in zip(pending, vectors, strict=True):
                    await self._ledger.put_embedding(item.text_hash, model, vector)
                done += len(pending)
                if len(pending) < _BATCH:
                    break
        return done
