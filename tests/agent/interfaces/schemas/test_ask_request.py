from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.interfaces.schemas import AskRequest


def test_only_a_question():
    assert AskRequest(q="노트북 며칠 안에 취소?").q.startswith("노트북")
    with pytest.raises(ValidationError):
        AskRequest(q="")
