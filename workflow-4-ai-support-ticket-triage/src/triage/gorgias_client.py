"""Pulls tickets from Gorgias and maps them into the same Ticket shape
io_utils.load_tickets() produces from a CSV, so run_batch() and everything
downstream doesn't care whether a ticket came from a file or a live helpdesk.
"""

from __future__ import annotations

import os

import httpx

from .io_utils import Ticket
from .notifications import notify_slack

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


def _raise_verbose(response: httpx.Response, action: str, raw_id: str) -> None:
    """response.raise_for_status() alone drops the response body -- Gorgias
    puts the actual validation error there (e.g. which field was missing),
    which is what actually makes a 400 fast to diagnose."""
    if response.status_code >= 400:
        raise httpx.HTTPStatusError(
            f"{response.status_code} error {action} ticket {raw_id}: {response.text}",
            request=response.request,
            response=response,
        )


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


def has_ai_triage_note(mapped_ticket_id: str) -> bool:
    """Used by the backfill script to skip a ticket that's already been
    processed -- avoids both a duplicate note and a wasted Claude call on
    a re-run, without needing a separate state file to track what's done."""
    raw_id = mapped_ticket_id.removeprefix("GOR-")
    with _client() as client:
        response = client.get(f"/tickets/{raw_id}/messages")
        response.raise_for_status()
        return any(
            (message.get("body_text") or "").startswith("[AI Triage]")
            for message in response.json().get("data", [])
        )


def format_triage_note(result) -> str:
    """Shared by the webhook (per-ticket, real-time) and the backfill script
    (batch, one-off) so a note looks the same regardless of which path
    produced it.

    Flagged tickets can now carry a draft too (a starting point, not a
    ready-to-send reply) -- branch on needs_human_review, not on whether a
    draft exists, so a flagged ticket's warning is never silently dropped
    just because the model also drafted something for it.
    """
    header = f"[AI Triage] category={result.category} urgency={result.urgency} confidence={result.confidence:.0%}"
    if result.needs_human_review:
        parts = [f"{header} -- FLAGGED FOR HUMAN REVIEW", f"Reason: {result.review_reason}"]
        if result.draft_reply:
            parts.append(f"Suggested starting point (needs review, not ready to send):\n\n{result.draft_reply}")
        return "\n\n".join(parts)
    return f"{header}\n\nSuggested reply (review before sending):\n\n{result.draft_reply}"


def post_internal_note(mapped_ticket_id: str, text: str) -> None:
    """Write the AI's triage result back onto the ticket as an internal
    note -- visible to agents in their normal Gorgias view, never sent to
    the customer. This is the human-in-the-loop handoff: an agent reviews
    and sends it themselves rather than the system auto-sending.

    mapped_ticket_id is our "GOR-<id>" form (Ticket.ticket_id /
    TriageResult.ticket_id) -- strip the prefix to get the raw Gorgias id
    the API expects in the URL.
    """
    raw_id = mapped_ticket_id.removeprefix("GOR-")
    with _client() as client:
        response = client.post(
            f"/tickets/{raw_id}/messages",
            json={
                "channel": "internal-note",
                "via": "internal-note",
                "from_agent": True,
                "sender": {"email": os.environ["GORGIAS_EMAIL"]},
                "body_text": text,
            },
        )
        _raise_verbose(response, "posting note for", raw_id)


def update_ticket_flags(mapped_ticket_id: str, tags: list[str], priority: str | None = None) -> None:
    """Tag (and optionally bump the priority of) a ticket so a flagged item
    surfaces in views/queues agents already watch -- an internal note alone
    does nothing if no one is looking at that specific ticket.

    Gorgias's ticket-update endpoint replaces the tags list wholesale, so
    fetch the ticket's current tags first and merge rather than clobbering
    whatever other automations or agents already tagged it with.
    """
    raw_id = mapped_ticket_id.removeprefix("GOR-")
    with _client() as client:
        current = client.get(f"/tickets/{raw_id}")
        current.raise_for_status()
        existing_tags = current.json().get("tags", [])
        existing_names = {t["name"] for t in existing_tags}
        merged_tags = existing_tags + [{"name": name} for name in tags if name not in existing_names]

        payload: dict = {"tags": merged_tags}
        if priority is not None:
            payload["priority"] = priority

        response = client.put(f"/tickets/{raw_id}", json=payload)
        _raise_verbose(response, "updating", raw_id)


def surface_flagged_ticket(customer_name: str, result) -> None:
    """The single source of truth for "what happens to a flagged ticket" --
    shared by the webhook (real-time) and the backfill script (one-off
    batch) so old and new tickets get identical treatment. No-op if the
    result wasn't flagged.

    Every flagged ticket gets tagged so it surfaces in a saved Gorgias
    view. The genuinely urgent ones (high urgency, not just "needs a
    human") additionally get priority bumped and an optional Slack ping,
    rather than relying on someone happening to check that view.
    """
    if not result.needs_human_review:
        return

    is_urgent = result.urgency == "high"
    update_ticket_flags(result.ticket_id, tags=["ai-flagged"], priority="high" if is_urgent else None)

    if is_urgent:
        notify_slack(
            f"[URGENT] Ticket {result.ticket_id} ({customer_name}) flagged for human review "
            f"-- {result.category}. Reason: {result.review_reason}"
        )
