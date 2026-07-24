"""CSV read/write helpers. Kept separate from pipeline.py so the batch
orchestration logic isn't coupled to a specific input/output format --
swapping this for a Shopify/Gorgias API pull later only touches this file.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .schema import TriageResult


@dataclass
class Ticket:
    ticket_id: str
    customer_name: str
    channel: str
    text: str


def load_tickets(csv_path: str | Path) -> list[Ticket]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            Ticket(
                ticket_id=row["ticket_id"],
                customer_name=row.get("customer_name", ""),
                channel=row.get("channel", "unknown"),
                text=row["text"],
            )
            for row in reader
        ]


def write_results(results: list[TriageResult], out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ticket_id", "sentiment", "urgency", "category", "order_number",
        "product_name", "issue_summary", "confidence", "needs_human_review",
        "review_reason", "draft_reply",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "ticket_id": r.ticket_id,
                "sentiment": r.sentiment,
                "urgency": r.urgency,
                "category": r.category,
                "order_number": r.entities.order_number,
                "product_name": r.entities.product_name,
                "issue_summary": r.issue_summary,
                "confidence": r.confidence,
                "needs_human_review": r.needs_human_review,
                "review_reason": r.review_reason,
                "draft_reply": r.draft_reply,
            })


def write_failures(failures: list, out_path: str | Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ticket_id", "error", "attempts"])
        writer.writeheader()
        for fail in failures:
            writer.writerow({
                "ticket_id": fail.ticket_id,
                "error": fail.error,
                "attempts": fail.attempts,
            })
