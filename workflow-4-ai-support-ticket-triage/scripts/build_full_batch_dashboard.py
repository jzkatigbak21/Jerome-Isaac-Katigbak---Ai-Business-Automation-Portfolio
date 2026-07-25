"""One-off: join a results.csv back with the original ticket text/customer/
channel (data/sample_tickets.csv doesn't round-trip through results.csv --
see io_utils.write_results' fieldnames) and inject the result as a CSV-
sourced dataset tab into dashboard.html. Parameterized by --dataset-key so
this covers both the full 300-row batch and the 20-row synthetic smoke
test -- whichever tab you target, the other two tabs are left untouched.

No API calls here: this only reads two CSVs already produced by a prior
`python -m src.cli` run and writes dashboard.html.

Usage:
    # Full 300-row batch (no --limit)
    python -m src.cli --input data/sample_tickets.csv --out-dir out --verbose
    python scripts/build_full_batch_dashboard.py

    # 20-row synthetic smoke test
    python -m src.cli --input data/sample_tickets.csv --out-dir out --limit 20 --verbose
    python scripts/build_full_batch_dashboard.py --dataset-key synthetic --label "Synthetic Dataset" --min-rows 15
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TICKETS_PATH = Path("data/sample_tickets.csv")
RESULTS_PATH = Path("out/results.csv")
DASHBOARD_PATH = Path("dashboard.html")


def _load_ticket_text() -> dict[str, dict]:
    with TICKETS_PATH.open(newline="", encoding="utf-8") as f:
        return {row["ticket_id"]: row for row in csv.DictReader(f)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-key", default="full300", help="DATASETS key in dashboard.html to write/replace.")
    parser.add_argument("--label", default="Full 300-Row Batch", help="Tab label shown in the dashboard.")
    parser.add_argument(
        "--min-rows", type=int, default=250,
        help="Sanity floor on out/results.csv row count before injecting (catches a stale/partial run).",
    )
    args = parser.parse_args()

    tickets_by_id = _load_ticket_text()

    with RESULTS_PATH.open(newline="", encoding="utf-8") as f:
        results = list(csv.DictReader(f))

    if len(results) < args.min_rows:
        print(
            f"out/results.csv only has {len(results)} rows -- expected at least {args.min_rows}. "
            "Run src.cli first to (re)generate it.",
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
        f'    {args.dataset_key}: {{\n'
        f'      label: "{args.label}",\n'
        f'      sub: "{len(rows)} template-generated tickets",\n'
        f'      live: false,\n'
        f'      tickets: {json.dumps(rows, indent=2)},\n'
        f'    }},\n'
    )

    start_marker = f"    {args.dataset_key}: {{\n"
    block_close_marker = "\n    },\n"  # this key's OWN closing brace, not the whole DATASETS object's
    datasets_close_marker = "\n  };"

    start = html.find(start_marker)
    if start != -1:
        # Re-run: replace just this key's own block. Bug fixed here: this
        # used to search for the whole DATASETS object's closing '};',
        # which only worked by accident when this key happened to be last
        # -- for any earlier key, it silently deleted every key after it.
        end = html.index(block_close_marker, start) + len(block_close_marker)
        html = html[:start] + new_dataset + html[end:]
    else:
        # First run for this key: insert right before the DATASETS object's
        # closing '};'. rindex, not index -- CHANNEL_LABEL/CATEGORY_LABEL
        # above DATASETS in this file close the same way, so the *last*
        # match is the one we want.
        close = html.rindex(datasets_close_marker)
        html = html[:close] + "\n" + new_dataset.rstrip("\n") + html[close:]

    DASHBOARD_PATH.write_text(html, encoding="utf-8")

    print(f"Injected {len(rows)} tickets into dashboard.html as dataset '{args.dataset_key}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
