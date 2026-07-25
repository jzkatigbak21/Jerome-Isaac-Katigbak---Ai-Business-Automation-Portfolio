"""Verifies the Gorgias -> Ticket mapping without hitting the real API.

Uses httpx.MockTransport to fake the two endpoints the client calls
(list tickets, then list messages per ticket), so the suite runs offline.
"""

from __future__ import annotations

import json

import httpx
import pytest

from src.triage.gorgias_client import fetch_tickets, post_internal_note

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
}


posted_messages: list[dict] = []


def _mock_handler(request: httpx.Request) -> httpx.Response:
    if request.method == "GET" and request.url.path == "/api/tickets":
        return httpx.Response(200, json=TICKETS_PAGE)
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
    assert "category=defect" in body["body_text"]


def test_post_internal_note_raises_on_error_response():
    with pytest.raises(httpx.HTTPStatusError):
        post_internal_note("GOR-999", "irrelevant")
