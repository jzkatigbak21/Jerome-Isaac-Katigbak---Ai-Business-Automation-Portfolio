"""Typed contracts for what the model must return.

Pydantic validates the JSON Claude returns so a malformed or partial
response fails loudly at parse time instead of silently corrupting a
downstream CSV.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Sentiment = Literal["positive", "neutral", "negative"]
Urgency = Literal["low", "medium", "high"]
Category = Literal["shipping", "defect", "refund", "praise", "question", "account", "other"]


class Entities(BaseModel):
    order_number: str | None = None
    product_name: str | None = None


class TriageResult(BaseModel):
    ticket_id: str
    sentiment: Sentiment
    urgency: Urgency
    category: Category
    entities: Entities
    issue_summary: str = Field(..., description="One-sentence plain summary of the issue.")
    confidence: float = Field(..., ge=0.0, le=1.0)
    needs_human_review: bool
    review_reason: str | None = None
    draft_reply: str | None = None

    @field_validator("review_reason")
    @classmethod
    def reason_required_if_flagged(cls, v, info):
        if info.data.get("needs_human_review") and not v:
            return "Model flagged for review without a stated reason."
        return v


class ProcessingFailure(BaseModel):
    ticket_id: str
    error: str
    attempts: int
