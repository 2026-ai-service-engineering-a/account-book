from __future__ import annotations

from typing import NewType

# agent가 올린 쓰기 제안의 식별자. 다른 식별자 자리에 넘기면 mypy가 막는다(rules 5.3).
ProposalId = NewType("ProposalId", str)
