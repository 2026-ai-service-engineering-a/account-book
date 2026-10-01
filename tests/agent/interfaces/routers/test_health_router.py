from __future__ import annotations

from tests.agent.conftest import FakeModel
from tests.agent.interfaces.conftest import client_with


def test_up_without_calling_the_model():
    model = FakeModel()
    assert client_with(model).get("/healthz").json() == {"status": "ok"}
    assert model.prompts == []
