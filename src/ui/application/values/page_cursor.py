from __future__ import annotations

from typing import NewType

# 목록의 다음 쪽. api가 주는 불투명한 문자열이라 화면은 풀어 보지 않는다.
PageCursor = NewType("PageCursor", str)
