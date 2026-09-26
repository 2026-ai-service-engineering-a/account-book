from __future__ import annotations

from typing import NewType

# 결제수단의 식별자. 다른 식별자 자리에 잘못 넘기면 mypy가 막는다(development-rules 5.3).
AccountId = NewType("AccountId", str)
