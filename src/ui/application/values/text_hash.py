from __future__ import annotations

from typing import NewType

# 색인 텍스트의 해시. 임베딩은 거래가 아니라 이 해시에 붙는다 —
# 같은 가맹점 백 건이 벡터 하나를 나눠 쓴다.
TextHash = NewType("TextHash", str)
