"""Verifies retry-on-failure behavior without hitting the real API.

These mock anthropic.Anthropic().messages.create so the suite runs offline
and asserts: (1) transient errors are retried and eventually succeed, and
(2) a non-retryable error is not retried.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import anthropic
import httpx
import pytest

from src.triage.client import TriageClient
from src.triage.schema import TriageResult


def _fake_request():
    return httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _fake_response(status_code: int):
    return httpx.Response(status_code, request=_fake_request())


def _tool_use_response(ticket_id: str = "T-1"):
    block = MagicMock()
    block.type = "tool_use"
    block.input = {
        "ticket_id": ticket_id,
        "sentiment": "negative",
        "urgency": "high",
        "category": "defect",
        "entities": {"order_number": "123456", "product_name": "Trail Runner Sneakers"},
        "issue_summary": "Product arrived broken.",
        "confidence": 0.92,
        "needs_human_review": False,
        "review_reason": None,
        "draft_reply": "Hi there, sorry about that -- The Support Team",
    }
    response = MagicMock()
    response.content = [block]
    return response


@patch("time.sleep", return_value=None)  # skip real backoff delays in tests
@patch("anthropic.resources.messages.Messages.create")
def test_retries_on_rate_limit_then_succeeds(mock_create, _mock_sleep):
    rate_limit_error = anthropic.RateLimitError(
        "rate limited", response=_fake_response(429), body={"error": "rate_limited"}
    )
    mock_create.side_effect = [rate_limit_error, _tool_use_response()]

    client = TriageClient(api_key="test-key")
    result = client.classify("system", "user prompt", ticket_id="T-1")

    assert isinstance(result, TriageResult)
    assert result.category == "defect"
    assert mock_create.call_count == 2


@patch("time.sleep", return_value=None)  # skip real backoff delays in tests
@patch("anthropic.resources.messages.Messages.create")
def test_gives_up_after_max_attempts(mock_create, _mock_sleep):
    mock_create.side_effect = anthropic.RateLimitError(
        "rate limited", response=_fake_response(429), body={"error": "rate_limited"}
    )

    client = TriageClient(api_key="test-key")
    with pytest.raises(anthropic.RateLimitError):
        client.classify("system", "user prompt", ticket_id="T-1")

    assert mock_create.call_count == 5


@patch("anthropic.resources.messages.Messages.create")
def test_does_not_retry_non_retryable_error(mock_create):
    mock_create.side_effect = anthropic.BadRequestError(
        "bad request", response=_fake_response(400), body={"error": "bad_request"}
    )

    client = TriageClient(api_key="test-key")
    with pytest.raises(anthropic.BadRequestError):
        client.classify("system", "user prompt", ticket_id="T-1")

    assert mock_create.call_count == 1
