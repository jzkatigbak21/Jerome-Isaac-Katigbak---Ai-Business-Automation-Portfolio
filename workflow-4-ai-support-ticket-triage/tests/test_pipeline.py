"""Tests the batch orchestration and safety-net flagging logic in isolation
from the network -- run_batch is exercised against a fake TriageClient so
these run instantly and offline.
"""

from __future__ import annotations

from src.triage.io_utils import Ticket
from src.triage.pipeline import _apply_safety_net, run_batch
from src.triage.schema import Entities, TriageResult


def _make_result(**overrides) -> TriageResult:
    defaults = dict(
        ticket_id="T-1",
        sentiment="neutral",
        urgency="low",
        category="question",
        entities=Entities(order_number=None, product_name=None),
        issue_summary="Customer has a question.",
        confidence=0.95,
        needs_human_review=False,
        review_reason=None,
        draft_reply="Hi! Sure -- The Support Team",
    )
    defaults.update(overrides)
    return TriageResult(**defaults)


def test_safety_net_flags_escalation_keywords_even_if_model_did_not():
    ticket = Ticket("T-1", "Jane Doe", "email", "If this isn't fixed I'm calling my lawyer.")
    result = _make_result(needs_human_review=False)

    flagged = _apply_safety_net(ticket, result)

    assert flagged.needs_human_review is True
    assert "escalation keyword" in flagged.review_reason
    assert flagged.draft_reply is None


def test_safety_net_flags_low_confidence():
    ticket = Ticket("T-2", "Jane Doe", "email", "Something about my order maybe?")
    result = _make_result(confidence=0.4, needs_human_review=False)

    flagged = _apply_safety_net(ticket, result)

    assert flagged.needs_human_review is True
    assert "confidence" in flagged.review_reason


def test_safety_net_leaves_clean_tickets_alone():
    ticket = Ticket("T-3", "Jane Doe", "email", "Love the product, thanks!")
    result = _make_result(confidence=0.95, needs_human_review=False)

    unchanged = _apply_safety_net(ticket, result)

    assert unchanged.needs_human_review is False
    assert unchanged.draft_reply == result.draft_reply


class _FailingClient:
    """Fails on odd-numbered tickets, succeeds on even ones."""

    def classify(self, system_prompt, user_prompt, ticket_id):
        n = int(ticket_id.split("-")[1])
        if n % 2 == 1:
            raise RuntimeError(f"simulated failure for {ticket_id}")
        return _make_result(ticket_id=ticket_id)


def test_run_batch_isolates_failures_from_successes():
    tickets = [Ticket(f"T-{i}", "Name", "email", "text") for i in range(1, 6)]

    outcome = run_batch(tickets, _FailingClient(), max_workers=3)

    assert len(outcome.results) == 2  # T-2, T-4
    assert len(outcome.failures) == 3  # T-1, T-3, T-5
    assert {f.ticket_id for f in outcome.failures} == {"T-1", "T-3", "T-5"}
