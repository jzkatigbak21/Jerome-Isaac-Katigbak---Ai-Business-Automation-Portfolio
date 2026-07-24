"""Pulls tickets from Gorgias and maps them into the same Ticket shape
io_utils.load_tickets() produces from a CSV, so run_batch() and everything
downstream doesn't care whether a ticket came from a file or a live helpdesk.
"""

from __future__ import annotations

import os

import httpx

from .io_utils import Ticket

GORGIAS_TIMEOUT_SECONDS = 15.0


def _client() -> httpx.Client:
    subdomain = os.environ["GORGIAS_SUBDOMAIN"]
    email = os.environ["GORGIAS_EMAIL"]
    api_key = os.environ["GORGIAS_API_KEY"]
    return httpx.Client(
        base_url=f"https://{subdomain}.gorgias.com/api",
        auth=(email, api_key),
        timeout=GORGIAS_TIMEOUT_SECONDS,
    )


def _first_customer_message(client: httpx.Client, ticket_id: int) -> dict | None:
    """The ticket-list/ticket-detail endpoints don't include message bodies --
    fetch the thread and return the first message actually authored by the
    customer (skipping anything the "agent" side sent, e.g. an auto-reply)."""
    response = client.get(
        f"/tickets/{ticket_id}/messages",
        params={"order_by": "created_datetime:asc"},
    )
    response.raise_for_status()
    for message in response.json().get("data", []):
        if not message.get("from_agent", False):
            return message
    return None


def _map_ticket(client: httpx.Client, raw: dict) -> Ticket | None:
    """Shared by fetch_tickets() (batch) and fetch_single_ticket() (webhook)
    so both entry points build a Ticket the same way."""
    message = _first_customer_message(client, raw["id"])
    if message is None:
        return None  # no customer-authored message yet -- nothing to triage

    sender = message.get("sender") or {}
    customer = raw.get("customer") or {}
    customer_name = sender.get("name") or customer.get("email", "Unknown")

    return Ticket(
        ticket_id=f"GOR-{raw['id']}",
        customer_name=customer_name,
        channel=raw.get("channel", "unknown"),
        text=(message.get("body_text") or "").strip(),
    )


def fetch_tickets(limit: int = 50) -> list[Ticket]:
    tickets: list[Ticket] = []
    with _client() as client:
        response = client.get("/tickets", params={"limit": limit})
        response.raise_for_status()
        for raw in response.json().get("data", []):
            ticket = _map_ticket(client, raw)
            if ticket is not None:
                tickets.append(ticket)
    return tickets


def fetch_single_ticket(ticket_id: str) -> Ticket | None:
    """Fetch and map one ticket by ID -- the webhook receiver's entry point,
    reacting to a single new ticket instead of polling a list."""
    with _client() as client:
        response = client.get(f"/tickets/{ticket_id}")
        response.raise_for_status()
        return _map_ticket(client, response.json())
