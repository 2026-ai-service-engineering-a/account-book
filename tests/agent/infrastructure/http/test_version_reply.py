from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.infrastructure.http.version_reply import VersionReply


def test_an_empty_version_is_an_unknown_shape():
    assert VersionReply.model_validate({"version": "3f2a"}).version == "3f2a"
    with pytest.raises(ValidationError):
        VersionReply.model_validate({"version": ""})
