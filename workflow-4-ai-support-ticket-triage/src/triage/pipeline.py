"""Batch orchestration: fan the ticket list out across a bounded thread
pool (so we respect rate limits instead of firing hundreds of requests at
once), collect results, and separate successes / human-review / hard
failures so nothing silently disappears from a large run.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from tqdm import tqdm

from .client import TriageClient
from .io_utils import Ticket
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schema import ProcessingFailure, TriageResult

logger = logging.getLogger("triage.pipeline")

# Secondary safety net on top of the model's own needs_human_review flag --
# never trust a single point of judgment for anything with legal/PR/safety
# risk. If any of these terms show up, force a human-review flag even if
# the model didn't set one.
ESCALATION_KEYWORDS = re.compile(
    r"\b(lawyer|attorney|sue|lawsuit|chargeback|dispute the charge|bbb|"
    r"better business bureau|ftc|press|reporter|catch(?:es|ing)? fire|"
    r"burn(?:s|ed|ing)?|allerg(?:y|ic)|hospital)\b",
    re.IGNORECASE,
)
CONFIDENCE_FLOOR = 0.7


@dataclass
class BatchOutcome:
    results: list[TriageResult]
    failures: list[ProcessingFailure]


def _apply_safety_net(ticket: Ticket, result: TriageResult) -> TriageResult:
    reasons = []
    if ESCALATION_KEYWORDS.search(ticket.text):
        reasons.append("escalation keyword detected in raw message")
    if result.confidence < CONFIDENCE_FLOOR:
        reasons.append(f"model confidence {result.confidence:.2f} below floor {CONFIDENCE_FLOOR}")

    if reasons and not result.needs_human_review:
        combined_reason = "; ".join(reasons)
        logger.info("Safety net overrode model on %s: %s", ticket.ticket_id, combined_reason)
        return result.model_copy(update={
            "needs_human_review": True,
            "review_reason": combined_reason,
            "draft_reply": None,
        })
    return result


def _process_one(client: TriageClient, ticket: Ticket) -> TriageResult:
    user_prompt = build_user_prompt(ticket.ticket_id, ticket.customer_name, ticket.channel, ticket.text)
    result = client.classify(SYSTEM_PROMPT, user_prompt, ticket.ticket_id)
    return _apply_safety_net(ticket, result)


def run_batch(tickets: list[Ticket], client: TriageClient, max_workers: int = 5) -> BatchOutcome:
    results: list[TriageResult] = []
    failures: list[ProcessingFailure] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticket = {
            executor.submit(_process_one, client, ticket): ticket for ticket in tickets
        }
        for future in tqdm(as_completed(future_to_ticket), total=len(tickets), desc="Triaging tickets"):
            ticket = future_to_ticket[future]
            try:
                results.append(future.result())
            except Exception as exc:  # noqa: BLE001 - deliberately broad: one bad ticket must not kill the batch
                logger.error("Ticket %s failed after retries: %s", ticket.ticket_id, exc)
                failures.append(ProcessingFailure(
                    ticket_id=ticket.ticket_id,
                    error=str(exc),
                    attempts=5,
                ))

    return BatchOutcome(results=results, failures=failures)


def summarize(outcome: BatchOutcome, total: int) -> str:
    flagged = sum(1 for r in outcome.results if r.needs_human_review)
    auto_replied = sum(1 for r in outcome.results if r.draft_reply)
    by_category: dict[str, int] = {}
    for r in outcome.results:
        by_category[r.category] = by_category.get(r.category, 0) + 1

    lines = [
        f"Processed {len(outcome.results)}/{total} tickets ({len(outcome.failures)} failed after retries)",
        f"Auto-drafted replies: {auto_replied}",
        f"Flagged for human review: {flagged}",
        "By category: " + ", ".join(f"{k}={v}" for k, v in sorted(by_category.items())),
    ]
    return "\n".join(lines)
