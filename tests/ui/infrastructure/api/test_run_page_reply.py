from __future__ import annotations

from tests.ui.infrastructure.api.test_run_line_reply import LINE
from ui.infrastructure.api.run_page_reply import RunPageReply


def test_a_page_with_its_cursor():
    page = RunPageReply.model_validate({"items": [LINE], "next_cursor": "abc"}).page()
    assert [line.id for line in page.items] == ["r1"] and page.next_cursor == "abc"
