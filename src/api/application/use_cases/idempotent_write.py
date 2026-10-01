from __future__ import annotations

from collections.abc import Callable

from api.application.dto import StoredReply
from api.application.errors import IdempotencyKeyReused, RequestInProgress
from api.application.ports import UnitOfWork


class IdempotentWrite:
    """쓰기 하나를 멱등 키와 함께 한 트랜잭션에서 돌린다(api-contract 3장).

    | 처음 보는 키          | 실행하고, 응답을 키와 함께 저장한다 |
    | 같은 키 + 같은 본문    | 다시 실행하지 않고 저장된 응답을 돌려준다 |
    | 같은 키 + 다른 본문    | IdempotencyKeyReused |
    | 처리 중인 키          | RequestInProgress |

    실패(검증·확인·없음)는 저장하지 않는다. 트랜잭션이 통째로 되돌아가 키도 남지 않는다 —
    화면은 폼을 열 때 만든 키 하나로 고쳐서 다시 보내기 때문이다(transaction-form.md 4.2).
    """

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(
        self, key: str, request_hash: str, perform: Callable[[UnitOfWork], StoredReply]
    ) -> StoredReply:
        with self._unit_of_work() as uow:
            found = uow.idempotency.find(key)
            if found is not None:
                if found.request_hash != request_hash:
                    raise IdempotencyKeyReused
                if found.reply is None:
                    raise RequestInProgress
                return found.reply
            uow.idempotency.claim(key, request_hash)
            reply = perform(uow)
            uow.idempotency.complete(key, reply)
            uow.commit()
            return reply
