from __future__ import annotations

from starlette.requests import Request

from ui.interfaces.templating import fragment, is_htmx


def request(headers):
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request({"type": "http", "headers": raw})


def test_fragment_escapes_data():
    html = fragment("partials/chat_bubble.html", {"text": "<script>alert(1)</script>"})
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_is_htmx():
    assert is_htmx(request({"HX-Request": "true"}))
    assert not is_htmx(request({}))
