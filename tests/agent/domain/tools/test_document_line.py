from __future__ import annotations

import re

from agent.domain.tools import DocumentLine


def test_ref_is_short_and_stable_per_chunk():
    ref = DocumentLine.ref_for("paragraph_item:여신전문금융업법/19/1")
    assert re.fullmatch(r"d[0-9a-f]{6}", ref)
    assert ref == DocumentLine.ref_for("paragraph_item:여신전문금융업법/19/1")
    assert ref != DocumentLine.ref_for("paragraph_item:여신전문금융업법/19/2")
