"""One-off backfill: classify existing Gorgias tickets, post the result
back as an internal note, and surface flagged ones (tag, priority bump,
Slack ping) -- for tickets that predate the webhook's automatic handling
(src/webhook_server.py), or were only ever processed via the CSV/
--source gorgias batch path, which never wrote anything back into Gorgias.

Safe to re-run: tickets that already carry an "[AI Triage]" note (from a
prior run of this script, or the webhook) are skipped entirely -- no
duplicate note, and no wasted Claude call, since the skip check happens
before classification. New tickets since the last run still get
processed fresh.

--force bypasses that skip check and reclassifies every current ticket
regardless -- useful after a prompt change (e.g. flagged tickets now
getting a suggested draft) to refresh tickets that were already
processed under the old prompt. Two side effects worth knowing before
using it: (1) it posts an ADDITIONAL "[AI Triage]" note rather than
editing the old one, so an already-processed ticket ends up with more
than one such note in its thread; (2) surface_flagged_ticket() runs
again too, so already-urgent-and-flagged tickets get tagged/prioritized
again and get ANOTHER Slack ping, not just a fresh note.

Usage:
    python scripts/backfill_notes.py
    python scripts/backfill_notes.py --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.triage.client import TriageClient
from src.triage.gorgias_client import (
    fetch_tickets,
    format_triage_note,
    has_ai_triage_note,
    post_internal_note,
    surface_flagged_ticket,
)
from src.triage.pipeline import process_one


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--force", action="store_true",
        help="Reprocess every ticket even if it already has an [AI Triage] note.",
    )
    args = parser.parse_args()

    load_dotenv()

    tickets = fetch_tickets()
    print(f"Fetched {len(tickets)} tickets from Gorgias\n")

    client = TriageClient()
    posted = 0
    skipped = 0
    for ticket in tickets:
        if not args.force and has_ai_triage_note(ticket.ticket_id):
            print(f"{ticket.ticket_id} ({ticket.customer_name}) -> already processed, skipping")
            skipped += 1
            continue

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

        outcome = "flagged for review" if result.needs_human_review else "auto-drafted"
        print(f"{ticket.ticket_id} ({ticket.customer_name}) -> {outcome} [{result.category}/{result.urgency}]")

    print(f"\nPosted notes on {posted}/{len(tickets)} tickets ({skipped} already processed, skipped).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
