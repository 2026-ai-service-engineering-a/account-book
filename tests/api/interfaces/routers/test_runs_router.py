from __future__ import annotations

from tests.api.conftest import FakeUnitOfWork, client_with
from tests.api.interfaces.schemas.test_run_write import run_body

KEY = {"Idempotency-Key": "run:0b6f0e4e-1c1e-4a51-9d2b-9a1f3c0d2e10"}


def test_records_a_run_with_its_tool_calls():
    uow = FakeUnitOfWork()
    response = client_with(uow=uow).post("/v1/runs", json=run_body(), headers=KEY)
    assert response.status_code == 201 and response.json() == {"id": run_body()["id"]}
    (run,) = uow.runs.rows.values()
    assert run.stop_reason == "answered" and run.tool_calls[0].tool == "summarize_spending"


def test_sending_it_again_with_the_same_key_keeps_one_row():
    uow = FakeUnitOfWork()
    client = client_with(uow=uow)
    first = client.post("/v1/runs", json=run_body(), headers=KEY)
    again = client.post("/v1/runs", json=run_body(), headers=KEY)
    assert first.status_code == again.status_code == 201 and len(uow.runs.rows) == 1


def test_missing_key_is_400_and_a_bad_body_is_422():
    client = client_with(uow=FakeUnitOfWork())
    assert client.post("/v1/runs", json=run_body()).status_code == 400
    bad = client.post("/v1/runs", json=run_body(seat="insights"), headers=KEY)
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "validation_error"


def test_a_proposal_is_read_confirmed_and_closed_only_while_waiting():
    uow = FakeUnitOfWork()
    client = client_with(uow=uow)
    waiting = run_body(seat="capture", flow="single", status="awaiting_confirmation")
    waiting["tool_calls"] = [{"call_id": "c2", "tool": "create_transaction", "args": {}}]
    run_id = waiting["id"]
    assert client.post("/v1/runs", json=waiting, headers=KEY).status_code == 201
    read = client.get(f"/v1/runs/{run_id}").json()
    assert read["status"] == "awaiting_confirmation" and read["created_at"]
    confirm = client.post(
        f"/v1/runs/{run_id}/confirm", json={"call_id": "c2"}, headers={"Idempotency-Key": "k1"}
    ).json()
    assert confirm["tool_calls"][0]["confirmed_at"]
    cancel = client.post(
        f"/v1/runs/{run_id}/close",
        json={"status": "aborted", "stop_reason": "cancelled"},
        headers={"Idempotency-Key": "k2"},
    ).json()
    assert cancel["status"] == "awaiting_confirmation"  # 확인된 제안은 취소되지 않는다
    done = client.post(
        f"/v1/runs/{run_id}/close",
        json={"status": "done", "stop_reason": "confirmed", "results": [
            {"call_id": "c2", "result": {"id": "t1"}}]},
        headers={"Idempotency-Key": "k3"},
    ).json()  # fmt: skip
    assert done["status"] == "done" and done["tool_calls"][0]["result"] == {"id": "t1"}


def test_an_unknown_run_is_404_not_found():
    response = client_with(uow=FakeUnitOfWork()).get("/v1/runs/nope")
    assert response.status_code == 404 and response.json()["error"]["code"] == "not_found"


def test_an_mcp_call_keeps_the_clients_name():
    uow = FakeUnitOfWork()
    client = client_with(uow=uow)
    body = run_body(seat="mcp", flow="direct", utterance="", model="external", client="Claude")
    assert client.post("/v1/runs", json=body, headers=KEY).status_code == 201
    read = client.get(f"/v1/runs/{body['id']}").json()
    assert (read["seat"], read["flow"], read["client"]) == ("mcp", "direct", "Claude")


def test_lists_runs_newest_first_and_filters():
    from tests.api.application.use_cases.test_list_runs import five_runs

    client = client_with(uow=five_runs())
    page = client.get("/v1/runs", params={"limit": 2}).json()
    assert [x["id"] for x in page["items"]] == ["r4", "r3"] and page["next_cursor"]
    rest = client.get("/v1/runs", params={"cursor": page["next_cursor"]}).json()
    assert [x["id"] for x in rest["items"]] == ["r2", "r1", "r0"]
    chat = client.get("/v1/runs", params={"seat": "chat", "status": "failed"}).json()
    assert [(x["id"], x["tool_count"]) for x in chat["items"]] == [("r2", 2)]


def test_an_unknown_seat_or_status_is_422():
    client = client_with(uow=FakeUnitOfWork())
    for params in ({"seat": "agent"}, {"status": "running"}, {"limit": 101}):
        assert client.get("/v1/runs", params=params).status_code == 422
