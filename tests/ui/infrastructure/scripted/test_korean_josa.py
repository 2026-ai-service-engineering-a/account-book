from __future__ import annotations

from ui.infrastructure.scripted.korean_josa import josa


def test_picks_by_final_consonant():
    assert josa("식비", "이", "가") == "식비가"
    assert josa("생활", "이", "가") == "생활이"
    assert josa("ABC", "이", "가") == "ABC가"
