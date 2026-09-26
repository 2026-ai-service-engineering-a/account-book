from __future__ import annotations


def test_reset_empties_and_refills(client):
    emptied = client.post(
        "/demo/reset", data={"filled": "false", "back": "/transactions"}, follow_redirects=False
    )
    assert emptied.headers["location"] == "/transactions"
    assert "아직 기록이 없어요" in client.get("/transactions").text
    client.post("/demo/reset", data={"filled": "true"})
    assert "아직 기록이 없어요" not in client.get("/transactions").text


def test_reset_never_redirects_off_site(client):
    moved = client.post(
        "/demo/reset", data={"filled": "true", "back": "//evil.example"}, follow_redirects=False
    )
    assert moved.headers["location"] == "/"
