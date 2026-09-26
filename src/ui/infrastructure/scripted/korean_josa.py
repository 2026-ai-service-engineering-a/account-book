"""조사 고르기. 받침이 있으면 앞의 것, 없으면 뒤의 것 — "식비가", "생활이"."""

from __future__ import annotations


def josa(word: str, with_final: str, without_final: str) -> str:
    last = word[-1:] or " "
    if "가" <= last <= "힣":
        has_final = (ord(last) - ord("가")) % 28 != 0
        return word + (with_final if has_final else without_final)
    return word + without_final
