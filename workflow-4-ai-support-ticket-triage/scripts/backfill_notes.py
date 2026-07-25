"""One-off backfill: classify existing Gorgias tickets, post the result
back as an internal note, and surface flagged ones (tag, priority bump,
Slack ping) -- for tickets that predate the webhook's automatic handling
(src/webhook_server.py), or were only ever processed via the CSV/
--source gorgias batch path, which never wrote anything back into Gorgias.

Not idempotent by design: every ticket fetch_tickets() returns gets
reclassified (a fresh Claude call) and gets a fresh note/tags/notification,
every run. Running it twice against the same tickets means double cost and
duplicate notes/tags/pings. Run it once.

Usage:
    python scripts/backfill_notes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.triage.client import TriageClient
from src.triage.gorgias_client import (
    fetch_tickets,
    format_triage_note,
    post_internal_note,
    surface_flagged_ticket,
)
from src.triage.pipeline import process_one


def main() -> int:
    load_dotenv()

    tickets = fetch_tickets()
    print(f"Fetched {len(tickets)} tickets from Gorgias\n")

    client = TriageClient()
    posted = 0
    for ticket in tickets:
        result = process_one(client, ticket)
        try:
            post_internal_note(result.ticket_id, format_triage_note(result))
            posted += 1
        except Exception as exc:  # noqa: BLE001 - one bad note write shouldn't stop the backfill
            print(f"  ! failed to post note for {ticket.ticket_id}: {exc}")

        try:
            surface_flagged_ticket(ticket.customer_name, result)
        except Exception as exc:  # noqa: BLE001 - same reasoning
            print(f"  ! failed to surface flagged ticket {ticket.ticket_id}: {exc}")

        outcome = "auto-drafted" if result.draft_reply else "flagged for review"
        print(f"{ticket.ticket_id} ({ticket.customer_name}) -> {outcome} [{result.category}/{result.urgency}]")

    print(f"\nPosted notes on {posted}/{len(tickets)} tickets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
