"""CLI entrypoint.

Usage:
    python -m src.cli --input data/sample_tickets.csv --out-dir out/
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
from src.triage.io_utils import load_tickets, write_failures, write_results
from src.triage.pipeline import run_batch, summarize


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Batch-triage support tickets with Claude.")
    parser.add_argument("--input", required=True, help="Path to input CSV of tickets.")
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
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in.", file=sys.stderr)
        return 1

    tickets = load_tickets(args.input)
    if args.limit is not None:
        tickets = tickets[:args.limit]
    print(f"Loaded {len(tickets)} tickets from {args.input}")

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
