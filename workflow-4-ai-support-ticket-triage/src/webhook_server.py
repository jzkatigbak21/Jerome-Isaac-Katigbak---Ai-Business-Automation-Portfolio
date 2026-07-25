"""Real-time webhook receiver -- the production-shape alternative to
`--source gorgias`'s periodic polling. A Gorgias Automation rule POSTs to
this endpoint the instant a ticket is created; each ticket is classified
individually as it arrives instead of waiting for a batch run.

Run locally:
    uvicorn src.webhook_server:app --reload --port 8000

Expose it to Gorgias (which is a live SaaS and can't reach localhost):
    ngrok http 8000

Then point a Gorgias Automation ("when a ticket is created" -> "call a
webhook") at https://<ngrok-id>.ngrok-free.app/webhook/gorgias.
"""

from __future__ import annotations

import csv
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

from .triage.client import TriageClient
from .triage.gorgias_client import (
    fetch_single_ticket,
    format_triage_note,
    post_internal_note,
    surface_flagged_ticket,
)
from .triage.pipeline import process_one

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("webhook")

app = FastAPI(title="Gorgias Ticket Triage Webhook")
_client: TriageClient | None = None

LIVE_RESULTS_PATH = Path("out/live_results.csv")

# Gorgias's automation builder lets you customize the webhook JSON body, so
# accept a few common shapes rather than assuming one exact structure --
# whatever the automation is configured to send.
_TICKET_ID_PATHS = (("ticket_id",), ("id",), ("ticket", "id"), ("data", "id"))


def _get_client() -> TriageClient:
    global _client
    if _client is None:
        _client = TriageClient()
    return _client


def _extract_ticket_id(payload: dict) -> str | None:
    for path in _TICKET_ID_PATHS:
        node = payload
        for key in path:
            if not isinstance(node, dict) or key not in node:
                node = None
                break
            node = node[key]
        if node is not None:
            return str(node)
    return None


def _already_processed(ticket_id: str) -> bool:
    """Webhooks are at-least-once, not exactly-once -- Gorgias retries a
    delivery if it doesn't get a fast enough 2xx back, which can replay a
    ticket we already finished (and already billed a Claude call for).
    Cheap dedup: has this ticket's mapped id already been logged?

    Not concurrency-safe against two near-simultaneous deliveries for the
    same ticket racing each other (that would need a lock or a DB unique
    constraint) -- fine for the retry-after-timeout case this guards
    against, which is the common one.
    """
    if not LIVE_RESULTS_PATH.exists():
        return False
    mapped_id = f"GOR-{ticket_id}"
    with LIVE_RESULTS_PATH.open(newline="", encoding="utf-8") as f:
        return any(row.get("ticket_id") == mapped_id for row in csv.DictReader(f))


def _append_result(result) -> None:
    LIVE_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    is_new = not LIVE_RESULTS_PATH.exists()
    with LIVE_RESULTS_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow([
                "received_at", "ticket_id", "category", "urgency",
                "needs_human_review", "draft_reply",
            ])
        writer.writerow([
            datetime.now(timezone.utc).isoformat(), result.ticket_id, result.category,
            result.urgency, result.needs_human_review, result.draft_reply or "",
        ])


@app.post("/webhook/gorgias")
async def gorgias_webhook(request: Request, x_webhook_secret: str | None = Header(default=None)):
    expected_secret = os.environ.get("WEBHOOK_SECRET")
    if expected_secret and x_webhook_secret != expected_secret:
        raise HTTPException(status_code=401, detail="invalid webhook secret")

    payload = await request.json()
    ticket_id = _extract_ticket_id(payload)
    if ticket_id is None:
        logger.warning("Webhook payload had no recognizable ticket id: %s", payload)
        return {"status": "ignored", "reason": "no ticket_id in payload"}

    if _already_processed(ticket_id):
        logger.info("Ticket %s already processed -- likely a webhook retry, skipping", ticket_id)
        return {"status": "duplicate", "ticket_id": ticket_id}

    ticket = fetch_single_ticket(ticket_id)
    if ticket is None:
        logger.info("Ticket %s has no customer-authored message yet -- skipping", ticket_id)
        return {"status": "skipped", "ticket_id": ticket_id}

    result = process_one(_get_client(), ticket)
    _append_result(result)

    outcome = "auto-drafted" if result.draft_reply else "flagged for review"
    logger.info(
        "Ticket %s (%s) -> %s [%s/%s]",
        ticket.ticket_id, ticket.customer_name, outcome, result.category, result.urgency,
    )

    try:
        post_internal_note(result.ticket_id, format_triage_note(result))
    except Exception:
        # The classification itself already succeeded and is logged --
        # don't fail the whole webhook response just because Gorgias
        # rejected the note write (e.g. a transient error on their side).
        logger.exception("Failed to post internal note for %s", result.ticket_id)

    try:
        surface_flagged_ticket(ticket.customer_name, result)
    except Exception:
        # Same reasoning as the note write above: this is a best-effort
        # visibility step, not the classification itself -- don't fail
        # the response over a Gorgias-side tag/priority/Slack error.
        logger.exception("Failed to surface flagged ticket %s", result.ticket_id)

    return {"status": "processed", "ticket_id": ticket.ticket_id, "outcome": outcome}


@app.get("/health")
async def health():
    return {"status": "ok"}
