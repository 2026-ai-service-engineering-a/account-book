from __future__ import annotations

from api.application.ports import DocumentRepository
from tests.api.fake_documents import FakeDocuments


def test_fake_fills_the_port():
    port: DocumentRepository = FakeDocuments()
    assert port is not None
