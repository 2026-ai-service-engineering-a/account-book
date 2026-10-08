from __future__ import annotations

from ui.application.ports import DocumentAnswerer
from ui.infrastructure.memory import MemoryDocumentGateway
from ui.infrastructure.scripted import ScriptedDocumentAnswerer


def test_stand_in_fills_the_port():
    port: DocumentAnswerer = ScriptedDocumentAnswerer(MemoryDocumentGateway())
    assert port is not None
