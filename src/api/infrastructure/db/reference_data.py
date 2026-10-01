"""기준 데이터 — 처음 뜰 때 있어야 하는 카테고리와 결제수단.

id는 ui의 메모리 대역과 같다. 거래가 api로 옮겨 와도 화면·에이전트·평가 세트가 같은 id를 쓴다.
"""

from __future__ import annotations

# (id, 이름, 방향)
CATEGORIES: tuple[tuple[str, str, str], ...] = (
    ("food", "식비", "expense"),
    ("cafe", "카페", "expense"),
    ("transport", "교통", "expense"),
    ("living", "생활", "expense"),
    ("housing", "주거", "expense"),
    ("etc", "기타", "expense"),
    ("salary", "급여", "income"),
    ("other_income", "기타수입", "income"),
)

# (id, 이름, 종류)
ACCOUNTS: tuple[tuple[str, str, str], ...] = (
    ("card", "카드", "card"),
    ("cash", "현금", "cash"),
    ("bank", "계좌이체", "bank"),
)
