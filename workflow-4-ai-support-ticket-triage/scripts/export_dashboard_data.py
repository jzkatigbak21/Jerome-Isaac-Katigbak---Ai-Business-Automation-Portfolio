"""One-off export: fetch current Gorgias tickets, classify each, and write
the result as dashboard-ready JSON -- for refreshing dashboard.html's live
dataset with whatever's actually in the account right now.

Read-only against Gorgias: unlike backfill_notes.py, this never posts a
note, tag, or Slack ping. It exists purely to produce the richer per-ticket
fields (customer name, original message text, sentiment, confidence,
summary, review reason) that the dashboard needs but neither results.csv
nor live_results.csv capture.

Each run reclassifies every ticket currently in the account -- one Claude
call per ticket -- since none of the fields the dashboard needs are
persisted anywhere between runs.

Usage:
    python scripts/export_dashboard_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.triage.client import TriageClient
from src.triage.gorgias_client import fetch_tickets
from src.triage.pipeline import process_one

OUT_PATH = Path("out/dashboard_live_tickets.json")
DASHBOARD_PATH = Path("dashboard.html")
DATASET_KEY = "gorgias"


def main() -> int:
    load_dotenv()

    tickets = fetch_tickets()
    print(f"Fetched {len(tickets)} tickets from Gorgias -- classifying each (1 Claude call per ticket)...\n")

    client = TriageClient()
    rows = []
    for ticket in tickets:
        result = process_one(client, ticket)
        rows.append({
            "id": result.ticket_id,
            "customer": ticket.customer_name,
            "channel": ticket.channel,
            "order": result.entities.order_number,
            "product": result.entities.product_name,
            "text": ticket.text,
            "sentiment": result.sentiment,
            "urgency": result.urgency,
            "category": result.category,
            "confidence": result.confidence,
            "resolved": not result.needs_human_review,
            "summary": result.issue_summary,
            "reviewReason": result.review_reason,
            "draft": result.draft_reply,
        })
        outcome = "flagged for review" if result.needs_human_review else "auto-drafted"
        print(f"{result.ticket_id} ({ticket.customer_name}) -> {outcome} [{result.category}/{result.urgency}]")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nWrote {len(rows)} tickets to {OUT_PATH}")

    html = DASHBOARD_PATH.read_text(encoding="utf-8")
    new_dataset = (
        f'    {DATASET_KEY}: {{\n'
        f'      label: "Live Gorgias Run",\n'
        f'      sub: "{len(rows)} real tickets · Shopify dev store",\n'
        f'      live: true,\n'
        f'      tickets: {json.dumps(rows, indent=2)},\n'
        f'    }},\n'
    )
    start_marker = f"    {DATASET_KEY}: {{\n"
    block_close_marker = "\n    },\n"  # this key's OWN closing brace, not the whole DATASETS object's
    datasets_close_marker = "\n  };"
    start = html.find(start_marker)
    if start != -1:
        end = html.index(block_close_marker, start) + len(block_close_marker)
        html = html[:start] + new_dataset + html[end:]
    else:
        close = html.rindex(datasets_close_marker)
        html = html[:close] + "\n" + new_dataset.rstrip("\n") + html[close:]
    DASHBOARD_PATH.write_text(html, encoding="utf-8")
    print(f"Injected {len(rows)} tickets into dashboard.html as dataset '{DATASET_KEY}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
