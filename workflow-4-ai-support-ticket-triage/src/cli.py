"""CLI entrypoint.

Usage:
    python -m src.cli --input data/sample_tickets.csv --out-dir out/
    python -m src.cli --source gorgias --out-dir out/
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.triage.client import TriageClient
from src.triage.gorgias_client import fetch_tickets, has_ai_triage_note
from src.triage.io_utils import load_tickets, write_failures, write_results
from src.triage.pipeline import run_batch, summarize


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Batch-triage support tickets with Claude.")
    parser.add_argument(
        "--source", choices=["csv", "gorgias"], default="csv",
        help="Where to pull tickets from.",
    )
    parser.add_argument("--input", help="Path to input CSV of tickets (required for --source csv).")
    parser.add_argument("--out-dir", default="out", help="Directory to write results into.")
    parser.add_argument(
        "--max-workers", type=int,
        default=int(os.environ.get("MAX_CONCURRENT_REQUESTS", 5)),
        help="Max concurrent API requests.",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Only process the first N tickets (useful for a cheap smoke test before a full run).",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Reprocess tickets even if they already have an [AI Triage] note "
             "(only relevant for --source gorgias; useful when tuning prompts against known tickets).",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in.", file=sys.stderr)
        return 1

    if args.source == "gorgias":
        missing = [v for v in ("GORGIAS_SUBDOMAIN", "GORGIAS_EMAIL", "GORGIAS_API_KEY") if v not in os.environ]
        if missing:
            print(f"Missing Gorgias env vars: {', '.join(missing)}. Add them to .env.", file=sys.stderr)
            return 1
        tickets = fetch_tickets()
        print(f"Pulled {len(tickets)} tickets from Gorgias")

        if not args.force:
            new_tickets = [t for t in tickets if not has_ai_triage_note(t.ticket_id)]
            skipped = len(tickets) - len(new_tickets)
            if skipped:
                print(f"Skipping {skipped} already-processed ticket(s) (use --force to reprocess)")
            tickets = new_tickets
    else:
        if not args.input:
            print("--input is required when --source csv", file=sys.stderr)
            return 1
        tickets = load_tickets(args.input)
        print(f"Loaded {len(tickets)} tickets from {args.input}")

    if args.limit is not None:
        tickets = tickets[:args.limit]

    client = TriageClient()
    outcome = run_batch(tickets, client, max_workers=args.max_workers)

    out_dir = Path(args.out_dir)
    write_results(outcome.results, out_dir / "results.csv")
    write_results(
        [r for r in outcome.results if r.needs_human_review],
        out_dir / "human_review_queue.csv",
    )
    if outcome.failures:
        write_failures(outcome.failures, out_dir / "failures.csv")

    print()
    print(summarize(outcome, total=len(tickets)))
    print(f"\nResults written to {out_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
