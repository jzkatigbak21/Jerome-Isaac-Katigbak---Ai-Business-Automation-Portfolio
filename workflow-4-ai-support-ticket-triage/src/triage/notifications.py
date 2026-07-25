"""Optional Slack ping for the genuinely urgent flagged tickets -- a tag
in a queue is easy to miss; a chargeback threat shouldn't wait for someone
to happen to check that view.

Gated on SLACK_WEBHOOK_URL being set. If it's unset, notify_slack() is a
no-op, so the rest of the pipeline never depends on Slack being configured.
"""

from __future__ import annotations

import os

import httpx

NOTIFY_TIMEOUT_SECONDS = 10.0


def notify_slack(text: str) -> None:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return
    response = httpx.post(webhook_url, json={"text": text}, timeout=NOTIFY_TIMEOUT_SECONDS)
    response.raise_for_status()
