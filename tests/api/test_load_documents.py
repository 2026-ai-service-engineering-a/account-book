from __future__ import annotations

from pathlib import Path

import pytest

from api import load_documents

pytestmark = pytest.mark.integration
LAWS = Path(__file__).parents[1] / "fixtures" / "ai" / "documents" / "laws"


def test_make_docs_twice_is_the_same(monkeypatch, migrated):
    # Settings가 가리키는 DB 대신 테스트가 만든 DB로 돌린다
    monkeypatch.setattr(load_documents, "create_db_engine", lambda _url: migrated)
    assert load_documents.main([str(LAWS)]) == 232
    assert load_documents.main([str(LAWS)]) == 232


def test_an_empty_folder_is_refused(tmp_path):
    with pytest.raises(SystemExit):
        load_documents.main([str(tmp_path)])
