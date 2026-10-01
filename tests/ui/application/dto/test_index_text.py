from __future__ import annotations

from ui.application.dto import IndexText
from ui.application.values import TextHash


def test_holds_hash_and_text():
    item = IndexText(TextHash("h"), "스타벅스")
    assert (item.text_hash, item.text) == ("h", "스타벅스")
