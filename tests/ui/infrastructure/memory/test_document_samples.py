from __future__ import annotations

from ui.infrastructure.memory.document_samples import SAMPLES


def test_a_few_clauses_with_their_source():
    assert len(SAMPLES) == 4
    assert all(path.startswith(title + "/") for path, title, _, _, _ in SAMPLES)
