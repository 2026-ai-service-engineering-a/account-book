from __future__ import annotations

from ui.application.ports import DocumentGateway
from ui.infrastructure.memory import MemoryDocumentGateway


def test_stand_in_fills_the_port():
    port: DocumentGateway = MemoryDocumentGateway()
    assert port is not None
