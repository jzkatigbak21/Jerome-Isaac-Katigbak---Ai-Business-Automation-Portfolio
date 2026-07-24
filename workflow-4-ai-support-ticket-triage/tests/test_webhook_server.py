"""Verifies the webhook receiver end-to-end (payload -> ticket lookup ->
classify -> CSV log) without a real Gorgias account, network access, or
Anthropic API key. Mocks the two I/O boundaries: gorgias_client and
TriageClient.classify.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.triage.io_utils import Ticket
from src.triage.schema import Entities, TriageResult
from src.webhook_server import _extract_ticket_id, app


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    # Redirect the results log into a scratch dir so tests don't touch out/
    monkeypatch.chdir(tmp_path)


@pytest.mark.parametrize("payload,expected", [
    ({"ticket_id": "123"}, "123"),
    ({"id": 456}, "456"),
    ({"ticket": {"id": 789}}, "789"),
    ({"data": {"id": "abc"}}, "abc"),
    ({"nothing_recognizable": True}, None),
])
def test_extract_ticket_id_accepts_common_payload_shapes(payload, expected):
    assert _extract_ticket_id(payload) == expected


def _fake_result(needs_human_review=False, draft_reply="Hi! -- The Support Team"):
    return TriageResult(
        ticket_id="GOR-1",
        sentiment="neutral",
        urgency="low",
        category="question",
        entities=Entities(order_number=None, product_name=None),
        issue_summary="Customer has a question.",
        confidence=0.9,
        needs_human_review=needs_human_review,
        review_reason="needs a human" if needs_human_review else None,
        draft_reply=None if needs_human_review else draft_reply,
    )


def test_webhook_processes_ticket_and_logs_result():
    ticket = Ticket("GOR-1", "Jane Doe", "email", "Does this ship internationally?")

    with patch("src.webhook_server.fetch_single_ticket", return_value=ticket), \
         patch("src.webhook_server.process_one", return_value=_fake_result()):
        client = TestClient(app)
        response = client.post("/webhook/gorgias", json={"ticket_id": "1"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["outcome"] == "auto-drafted"

    from pathlib import Path
    log = Path("out/live_results.csv").read_text()
    assert "GOR-1" in log


def test_webhook_skips_ticket_with_no_customer_message():
    with patch("src.webhook_server.fetch_single_ticket", return_value=None):
        client = TestClient(app)
        response = client.post("/webhook/gorgias", json={"ticket_id": "999"})

    assert response.status_code == 200
    assert response.json()["status"] == "skipped"


def test_webhook_ignores_unrecognized_payload():
    client = TestClient(app)
    response = client.post("/webhook/gorgias", json={"nonsense": True})

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_webhook_rejects_bad_secret(monkeypatch):
    monkeypatch.setenv("WEBHOOK_SECRET", "correct-secret")
    client = TestClient(app)

    response = client.post(
        "/webhook/gorgias",
        json={"ticket_id": "1"},
        headers={"x-webhook-secret": "wrong"},
    )

    assert response.status_code == 401


def test_webhook_accepts_correct_secret():
    ticket = Ticket("GOR-2", "Jane Doe", "email", "Hello")

    with patch.dict("os.environ", {"WEBHOOK_SECRET": "correct-secret"}), \
         patch("src.webhook_server.fetch_single_ticket", return_value=ticket), \
         patch("src.webhook_server.process_one", return_value=_fake_result()):
        client = TestClient(app)
        response = client.post(
            "/webhook/gorgias",
            json={"ticket_id": "2"},
            headers={"x-webhook-secret": "correct-secret"},
        )

    assert response.status_code == 200
