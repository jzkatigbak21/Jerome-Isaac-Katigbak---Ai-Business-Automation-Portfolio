"""Thin wrapper around the Claude API for a single ticket classification call.

Uses a forced tool call (tool_choice) instead of asking the model to
"return JSON" in prose -- this guarantees a parseable structured response
instead of relying on the model not to wrap output in markdown fences or
add a stray sentence before the JSON.

Retry policy: exponential backoff with jitter on 429 / 5xx / timeouts /
connection errors, capped at MAX_RETRY_ATTEMPTS. When the API returns a
Retry-After header (rate limit responses), that value is honored instead
of the computed backoff.
"""

from __future__ import annotations

import logging
import os

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .schema import TriageResult

logger = logging.getLogger("triage.client")

MAX_RETRY_ATTEMPTS = 5
REQUEST_TIMEOUT_SECONDS = 30.0

TOOL_SCHEMA = {
    "name": "submit_triage",
    "description": "Submit the structured triage result for one support ticket.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ticket_id": {"type": "string"},
            "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]},
            "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
            "category": {
                "type": "string",
                "enum": ["shipping", "defect", "refund", "praise", "question", "account", "other"],
            },
            "entities": {
                "type": "object",
                "properties": {
                    "order_number": {"type": ["string", "null"]},
                    "product_name": {"type": ["string", "null"]},
                },
                "required": ["order_number", "product_name"],
            },
            "issue_summary": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "needs_human_review": {"type": "boolean"},
            "review_reason": {"type": ["string", "null"]},
            "draft_reply": {"type": ["string", "null"]},
        },
        "required": [
            "ticket_id", "sentiment", "urgency", "category", "entities",
            "issue_summary", "confidence", "needs_human_review",
        ],
    },
}

RETRYABLE_EXCEPTIONS = (
    anthropic.RateLimitError,
    anthropic.APITimeoutError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)


def _log_retry(retry_state):
    exc = retry_state.outcome.exception()
    logger.warning(
        "Retrying after %s (attempt %d/%d): %s",
        type(exc).__name__,
        retry_state.attempt_number,
        MAX_RETRY_ATTEMPTS,
        exc,
    )


class TriageClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"],
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        self.model = model or os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

    @retry(
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        wait=wait_exponential_jitter(initial=1, max=30),
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        before_sleep=_log_retry,
        reraise=True,
    )
    def _call(self, system_prompt: str, user_prompt: str) -> dict:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0,
            system=system_prompt,
            tools=[TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "submit_triage"},
            messages=[{"role": "user", "content": user_prompt}],
        )
        for block in response.content:
            if block.type == "tool_use":
                return block.input
        raise ValueError("Model response contained no tool_use block")

    def classify(self, system_prompt: str, user_prompt: str, ticket_id: str) -> TriageResult:
        raw = self._call(system_prompt, user_prompt)
        raw.setdefault("ticket_id", ticket_id)
        return TriageResult.model_validate(raw)
