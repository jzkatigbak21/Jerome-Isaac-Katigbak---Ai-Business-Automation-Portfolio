"""One-off: join a full-batch results.csv back with the original ticket
text/customer/channel (data/sample_tickets.csv doesn't round-trip through
results.csv -- see io_utils.write_results' fieldnames) and inject the
result as a third dataset tab into dashboard.html, alongside the existing
synthetic (20-row) and Gorgias tabs -- neither of which this script touches.

No API calls here: this only reads two CSVs already produced by a prior
`python -m src.cli --input data/sample_tickets.csv --out-dir out --verbose`
run (no --limit, so all 300 rows are classified) and writes dashboard.html.

Usage:
    python -m src.cli --input data/sample_tickets.csv --out-dir out --verbose
    python scripts/build_full_batch_dashboard.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TICKETS_PATH = Path("data/sample_tickets.csv")
RESULTS_PATH = Path("out/results.csv")
DASHBOARD_PATH = Path("dashboard.html")

DATASET_KEY = "full300"


def _load_ticket_text() -> dict[str, dict]:
    with TICKETS_PATH.open(newline="", encoding="utf-8") as f:
        return {row["ticket_id"]: row for row in csv.DictReader(f)}


def main() -> int:
    tickets_by_id = _load_ticket_text()

    with RESULTS_PATH.open(newline="", encoding="utf-8") as f:
        results = list(csv.DictReader(f))

    if len(results) < 250:
        print(
            f"out/results.csv only has {len(results)} rows -- expected ~300. "
            "Run the full batch first (no --limit):\n"
            "  python -m src.cli --input data/sample_tickets.csv --out-dir out --verbose",
            file=sys.stderr,
        )
        return 1

    rows = []
    for r in results:
        ticket = tickets_by_id.get(r["ticket_id"])
        if ticket is None:
            continue
        rows.append({
            "id": r["ticket_id"],
            "customer": ticket["customer_name"],
            "channel": ticket["channel"],
            "order": r["order_number"] or None,
            "product": r["product_name"] or None,
            "text": ticket["text"],
            "sentiment": r["sentiment"],
            "urgency": r["urgency"],
            "category": r["category"],
            "confidence": float(r["confidence"]),
            "resolved": r["needs_human_review"] != "True",
            "summary": r["issue_summary"],
            "reviewReason": r["review_reason"] or None,
            "draft": r["draft_reply"] or None,
        })

    html = DASHBOARD_PATH.read_text(encoding="utf-8")

    new_dataset = (
        f'    {DATASET_KEY}: {{\n'
        f'      label: "Full 300-Row Batch",\n'
        f'      sub: "{len(rows)} template-generated tickets",\n'
        f'      live: false,\n'
        f'      tickets: {json.dumps(rows, indent=2)},\n'
        f'    }},\n'
    )

    start_marker = f"    {DATASET_KEY}: {{\n"
    close_marker = "\n  };"

    start = html.find(start_marker)
    if start != -1:
        # Re-run: replace the existing full300 block in place.
        end = html.index(close_marker, start)
        html = html[:start] + new_dataset.rstrip("\n") + html[end:]
    else:
        # First run: insert right before the DATASETS object's closing '};'.
        # rindex, not index -- CHANNEL_LABEL/CATEGORY_LABEL above DATASETS in
        # this file close the same way, so the *last* match is the one we want.
        close = html.rindex(close_marker)
        html = html[:close] + "\n" + new_dataset.rstrip("\n") + html[close:]

    DASHBOARD_PATH.write_text(html, encoding="utf-8")

    print(f"Injected {len(rows)} tickets into dashboard.html as dataset '{DATASET_KEY}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
