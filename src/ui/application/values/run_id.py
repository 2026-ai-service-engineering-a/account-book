from __future__ import annotations

from typing import NewType

# agent 실행 하나. 있으면 거래의 source가 agent가 된다.
RunId = NewType("RunId", str)
