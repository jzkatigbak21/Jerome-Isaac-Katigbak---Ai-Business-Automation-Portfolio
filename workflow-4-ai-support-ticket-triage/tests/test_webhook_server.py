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


def _fake_result(ticket_id="GOR-1", needs_human_review=False, draft_reply="Hi! -- The Support Team", urgency="low"):
    return TriageResult(
        ticket_id=ticket_id,
        sentiment="neutral",
        urgency=urgency,
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
         patch("src.webhook_server.process_one", return_value=_fake_result()), \
         patch("src.webhook_server.post_internal_note") as mock_note:
        client = TestClient(app)
        response = client.post("/webhook/gorgias", json={"ticket_id": "1"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["outcome"] == "auto-drafted"

    from pathlib import Path
    log = Path("out/live_results.csv").read_text()
    assert "GOR-1" in log

    # The AI's result is written back onto the ticket as an internal note,
    # so an agent sees it in their normal Gorgias view.
    mock_note.assert_called_once()
    note_ticket_id, note_text = mock_note.call_args[0]
    assert note_ticket_id == "GOR-1"
    assert "Hi! -- The Support Team" in note_text


def test_webhook_flagged_ticket_note_includes_review_reason():
    ticket = Ticket("GOR-4", "Jane Doe", "email", "This is unacceptable, third time contacting.")

    with patch("src.webhook_server.fetch_single_ticket", return_value=ticket), \
         patch("src.webhook_server.process_one", return_value=_fake_result(ticket_id="GOR-4", needs_human_review=True)), \
         patch("src.webhook_server.post_internal_note") as mock_note, \
         patch("src.webhook_server.update_ticket_flags"), \
         patch("src.webhook_server.notify_slack"):
        client = TestClient(app)
        response = client.post("/webhook/gorgias", json={"ticket_id": "4"})

    assert response.json()["outcome"] == "flagged for review"
    note_text = mock_note.call_args[0][1]
    assert "FLAGGED FOR HUMAN REVIEW" in note_text
    assert "needs a human" in note_text


def test_webhook_tags_flagged_ticket_without_bumping_priority_when_not_urgent():
    """Every flagged ticket gets tagged so it surfaces in a saved view --
    but priority is only bumped and Slack pinged for the genuinely urgent
    ones, not every flag."""
    ticket = Ticket("GOR-6", "Jane Doe", "email", "Can you clarify the return policy?")

    with patch("src.webhook_server.fetch_single_ticket", return_value=ticket), \
         patch("src.webhook_server.process_one",
               return_value=_fake_result(ticket_id="GOR-6", needs_human_review=True, urgency="medium")), \
         patch("src.webhook_server.post_internal_note"), \
         patch("src.webhook_server.update_ticket_flags") as mock_flags, \
         patch("src.webhook_server.notify_slack") as mock_slack:
        client = TestClient(app)
        client.post("/webhook/gorgias", json={"ticket_id": "6"})

    mock_flags.assert_called_once_with("GOR-6", tags=["ai-flagged"], priority=None)
    mock_slack.assert_not_called()


def test_webhook_bumps_priority_and_notifies_slack_for_urgent_flagged_ticket():
    ticket = Ticket("GOR-7", "Jane Doe", "email", "Third time emailing, disputing the charge.")

    with patch("src.webhook_server.fetch_single_ticket", return_value=ticket), \
         patch("src.webhook_server.process_one",
               return_value=_fake_result(ticket_id="GOR-7", needs_human_review=True, urgency="high")), \
         patch("src.webhook_server.post_internal_note"), \
         patch("src.webhook_server.update_ticket_flags") as mock_flags, \
         patch("src.webhook_server.notify_slack") as mock_slack:
        client = TestClient(app)
        client.post("/webhook/gorgias", json={"ticket_id": "7"})

    mock_flags.assert_called_once_with("GOR-7", tags=["ai-flagged"], priority="high")
    mock_slack.assert_called_once()
    assert "GOR-7" in mock_slack.call_args[0][0]
    assert "URGENT" in mock_slack.call_args[0][0]


def test_webhook_does_not_tag_or_notify_for_auto_drafted_ticket():
    """An auto-drafted (not flagged) ticket needs neither a tag nor a
    Slack ping -- there's nothing for a human to be surfaced to."""
    ticket = Ticket("GOR-8", "Jane Doe", "email", "Loved it, thanks!")

    with patch("src.webhook_server.fetch_single_ticket", return_value=ticket), \
         patch("src.webhook_server.process_one", return_value=_fake_result(ticket_id="GOR-8", urgency="high")), \
         patch("src.webhook_server.post_internal_note"), \
         patch("src.webhook_server.update_ticket_flags") as mock_flags, \
         patch("src.webhook_server.notify_slack") as mock_slack:
        client = TestClient(app)
        client.post("/webhook/gorgias", json={"ticket_id": "8"})

    mock_flags.assert_not_called()
    mock_slack.assert_not_called()


def test_webhook_note_post_failure_does_not_break_response():
    """A rejected/failed note write shouldn't take down an otherwise
    successful classification -- the result is already logged."""
    ticket = Ticket("GOR-5", "Jane Doe", "email", "Hello")

    with patch("src.webhook_server.fetch_single_ticket", return_value=ticket), \
         patch("src.webhook_server.process_one", return_value=_fake_result(ticket_id="GOR-5")), \
         patch("src.webhook_server.post_internal_note", side_effect=RuntimeError("Gorgias 500")):
        client = TestClient(app)
        response = client.post("/webhook/gorgias", json={"ticket_id": "5"})

    assert response.status_code == 200
    assert response.json()["status"] == "processed"


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


def test_webhook_deduplicates_retried_delivery():
    """Simulates Gorgias retrying a delivery for a ticket already processed
    -- the second call must not re-fetch or re-classify (which would
    double-bill Claude and could double-post a reply)."""
    ticket = Ticket("GOR-3", "Jane Doe", "email", "Where's my order?")

    with patch("src.webhook_server.fetch_single_ticket", return_value=ticket) as mock_fetch, \
         patch("src.webhook_server.process_one", return_value=_fake_result(ticket_id="GOR-3")) as mock_process, \
         patch("src.webhook_server.post_internal_note"):
        client = TestClient(app)

        first = client.post("/webhook/gorgias", json={"ticket_id": "3"})
        second = client.post("/webhook/gorgias", json={"ticket_id": "3"})

    assert first.json()["status"] == "processed"
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    assert mock_fetch.call_count == 1
    assert mock_process.call_count == 1

    from pathlib import Path
    log = Path("out/live_results.csv").read_text()
    assert log.count("GOR-3") == 1


def test_webhook_accepts_correct_secret():
    ticket = Ticket("GOR-2", "Jane Doe", "email", "Hello")

    with patch.dict("os.environ", {"WEBHOOK_SECRET": "correct-secret"}), \
         patch("src.webhook_server.fetch_single_ticket", return_value=ticket), \
         patch("src.webhook_server.process_one", return_value=_fake_result()), \
         patch("src.webhook_server.post_internal_note"):
        client = TestClient(app)
        response = client.post(
            "/webhook/gorgias",
            json={"ticket_id": "2"},
            headers={"x-webhook-secret": "correct-secret"},
        )

    assert response.status_code == 200
