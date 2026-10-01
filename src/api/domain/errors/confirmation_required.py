from __future__ import annotations


class ConfirmationRequired(Exception):
    """사람의 확인이 필요한 쓰기다(api-contract 4장). 412 confirmation_required.

    `AGENT_CONFIRM_THRESHOLD` 이상의 금액, 그리고 모든 삭제.
    """
