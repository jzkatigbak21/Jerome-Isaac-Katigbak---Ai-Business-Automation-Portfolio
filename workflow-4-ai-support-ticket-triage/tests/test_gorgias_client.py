"""Verifies the Gorgias -> Ticket mapping without hitting the real API.

Uses httpx.MockTransport to fake the two endpoints the client calls
(list tickets, then list messages per ticket), so the suite runs offline.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest

from src.triage.gorgias_client import (
    fetch_tickets,
    format_triage_note,
    has_ai_triage_note,
    post_internal_note,
    surface_flagged_ticket,
    update_ticket_flags,
)
from src.triage.schema import Entities, TriageResult

TICKETS_PAGE = {
    "data": [
        {"id": 101, "channel": "email", "customer": {"email": "karine.ruby@example.com"}},
        {"id": 102, "channel": "chat", "customer": {"email": "russel.winfield@example.com"}},
    ],
}

MESSAGES_BY_TICKET = {
    101: {
        "data": [
            {
                "from_agent": False,
                "sender": {"name": "Karine Ruby"},
                "body_text": "Order #1004 hasn't shipped yet, what's going on?",
            },
        ],
    },
    102: {
        # Only an agent auto-reply exists -- no customer message yet.
        "data": [
            {"from_agent": True, "sender": {"name": "Support Bot"}, "body_text": "We got your message!"},
        ],
    },
    103: {
        # Already backfilled: a prior [AI Triage] note is in the thread.
        "data": [
            {"from_agent": False, "sender": {"name": "Jane Doe"}, "body_text": "Where's my order?"},
            {"from_agent": True, "sender": {"name": "bot"}, "body_text": "[AI Triage] category=shipping urgency=low confidence=80%"},
        ],
    },
}


posted_messages: list[dict] = []
put_requests: list[dict] = []

TICKET_101_DETAIL = {
    "id": 101,
    "tags": [{"id": 1, "name": "ORDER-STATUS"}],
}


def _mock_handler(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path == "/api/tickets":
        return httpx.Response(200, json=TICKETS_PAGE)
    if request.method == "GET" and request.url.path == "/api/tickets/101":
        return httpx.Response(200, json=TICKET_101_DETAIL)
    if request.method == "GET" and request.url.path == "/api/tickets/888":
        return httpx.Response(404, json={"error": "not found"})
    if request.method == "PUT" and request.url.path == "/api/tickets/101":
        put_requests.append(json.loads(request.content))
        return httpx.Response(200, json={"id": 101})
    if request.method == "POST" and request.url.path == "/api/tickets/101/messages":
        posted_messages.append(json.loads(request.content))
        return httpx.Response(201, json={"id": 999})
    if request.method == "POST" and request.url.path == "/api/tickets/999/messages":
        return httpx.Response(404, json={"error": "not found"})
    for ticket_id, payload in MESSAGES_BY_TICKET.items():
        if request.method == "GET" and request.url.path == f"/api/tickets/{ticket_id}/messages":
            return httpx.Response(200, json=payload)
    raise AssertionError(f"unexpected request: {request.method} {request.url}")


@pytest.fixture(autouse=True)
def _patch_client(monkeypatch):
    import src.triage.gorgias_client as gorgias_client

    def fake_client():
        return httpx.Client(
            base_url="https://test-store.gorgias.com/api",
            transport=httpx.MockTransport(_mock_handler),
        )

    monkeypatch.setenv("GORGIAS_SUBDOMAIN", "test-store")
    monkeypatch.setenv("GORGIAS_EMAIL", "agent@example.com")
    monkeypatch.setenv("GORGIAS_API_KEY", "test-key")
    monkeypatch.setattr(gorgias_client, "_client", fake_client)
    posted_messages.clear()
    put_requests.clear()


def test_maps_customer_authored_message_into_ticket():
    tickets = fetch_tickets()

    assert len(tickets) == 1  # ticket 102 has no customer message and is skipped
    ticket = tickets[0]
    assert ticket.ticket_id == "GOR-101"
    assert ticket.customer_name == "Karine Ruby"
    assert ticket.channel == "email"
    assert ticket.text == "Order #1004 hasn't shipped yet, what's going on?"


def test_skips_tickets_with_no_customer_message():
    tickets = fetch_tickets()
    assert all(t.ticket_id != "GOR-102" for t in tickets)


def test_post_internal_note_strips_gor_prefix_and_sends_expected_body():
    post_internal_note("GOR-101", "[AI Triage] category=defect urgency=medium confidence=85%")

    assert len(posted_messages) == 1
    body = posted_messages[0]
    assert body["channel"] == "internal-note"
    assert body["from_agent"] is True
    assert body["sender"] == {"email": "agent@example.com"}  # matches the fixture's GORGIAS_EMAIL
    assert "category=defect" in body["body_text"]


def test_post_internal_note_raises_on_error_response():
    with pytest.raises(httpx.HTTPStatusError):
        post_internal_note("GOR-999", "irrelevant")


def test_update_ticket_flags_merges_without_clobbering_existing_tags():
    update_ticket_flags("GOR-101", tags=["ai-flagged"], priority="high")

    assert len(put_requests) == 1
    body = put_requests[0]
    names = {t["name"] for t in body["tags"]}
    assert names == {"ORDER-STATUS", "ai-flagged"}  # existing tag preserved, new one added
    assert body["priority"] == "high"


def test_update_ticket_flags_skips_duplicate_tag():
    update_ticket_flags("GOR-101", tags=["ORDER-STATUS"])  # already present

    body = put_requests[0]
    assert [t["name"] for t in body["tags"]].count("ORDER-STATUS") == 1


def test_update_ticket_flags_omits_priority_when_not_given():
    update_ticket_flags("GOR-101", tags=["ai-flagged"])

    assert "priority" not in put_requests[0]


def test_update_ticket_flags_raises_on_error_response():
    with pytest.raises(httpx.HTTPStatusError):
        update_ticket_flags("GOR-888", tags=["ai-flagged"])


def test_has_ai_triage_note_false_when_not_yet_processed():
    assert has_ai_triage_note("GOR-101") is False


def test_has_ai_triage_note_true_when_already_backfilled():
    assert has_ai_triage_note("GOR-103") is True


def _make_result(**overrides) -> TriageResult:
    defaults = dict(
        ticket_id="GOR-101",
        sentiment="negative",
        urgency="medium",
        category="account",
        entities=Entities(order_number=None, product_name=None),
        issue_summary="Customer needs help.",
        confidence=0.8,
        needs_human_review=True,
        review_reason="needs a human",
        draft_reply=None,
    )
    defaults.update(overrides)
    return TriageResult(**defaults)


def test_format_triage_note_ready_to_send_when_not_flagged():
    result = _make_result(needs_human_review=False, draft_reply="Hi! -- The Support Team")

    note = format_triage_note(result)

    assert "FLAGGED FOR HUMAN REVIEW" not in note
    assert "Suggested reply (review before sending)" in note
    assert "Hi! -- The Support Team" in note


def test_format_triage_note_flagged_without_draft_shows_reason_only():
    result = _make_result(needs_human_review=True, review_reason="chargeback threat", draft_reply=None)

    note = format_triage_note(result)

    assert "FLAGGED FOR HUMAN REVIEW" in note
    assert "chargeback threat" in note
    assert "Suggested starting point" not in note


def test_format_triage_note_flagged_with_draft_shows_both_never_drops_the_flag():
    result = _make_result(
        needs_human_review=True, review_reason="chargeback threat",
        draft_reply="Hi, sorry for the trouble -- we're looking into this now.",
    )

    note = format_triage_note(result)

    assert "FLAGGED FOR HUMAN REVIEW" in note
    assert "chargeback threat" in note
    assert "Suggested starting point (needs review, not ready to send)" in note
    assert "we're looking into this now" in note


def test_surface_flagged_ticket_is_noop_when_not_flagged():
    result = _make_result(needs_human_review=True, draft_reply=None)
    result = result.model_copy(update={"needs_human_review": False, "draft_reply": "Hi!"})

    with patch("src.triage.gorgias_client.notify_slack") as mock_slack:
        surface_flagged_ticket("Jane Doe", result)

    assert put_requests == []  # update_ticket_flags never called
    mock_slack.assert_not_called()


def test_surface_flagged_ticket_tags_only_when_not_urgent():
    result = _make_result(urgency="medium")

    with patch("src.triage.gorgias_client.notify_slack") as mock_slack:
        surface_flagged_ticket("Jane Doe", result)

    assert len(put_requests) == 1
    assert "ai-flagged" in {t["name"] for t in put_requests[0]["tags"]}
    assert "priority" not in put_requests[0]
    mock_slack.assert_not_called()


def test_surface_flagged_ticket_bumps_priority_and_notifies_when_urgent():
    result = _make_result(urgency="high", category="other", review_reason="chargeback threat")

    with patch("src.triage.gorgias_client.notify_slack") as mock_slack:
        surface_flagged_ticket("Jane Doe", result)

    assert put_requests[0]["priority"] == "high"
    mock_slack.assert_called_once()
    message = mock_slack.call_args[0][0]
    assert "GOR-101" in message and "Jane Doe" in message and "chargeback threat" in message
