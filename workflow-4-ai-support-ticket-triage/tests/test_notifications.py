"""Verifies notify_slack() is a true no-op when unconfigured, and posts
the expected payload when it is -- mocked via httpx.MockTransport so the
suite runs offline.
"""

from __future__ import annotations

import json

import httpx
import pytest

from src.triage.notifications import notify_slack

posted: list[dict] = []


def _mock_handler(request: httpx.Request) -> httpx.Response:
    posted.append(json.loads(request.content))
    return httpx.Response(200, text="ok")


@pytest.fixture(autouse=True)
def _reset():
    posted.clear()


def test_no_op_when_webhook_url_unset(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    monkeypatch.setattr(httpx, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not be called")))

    notify_slack("should not be sent")  # must not raise, must not call httpx.post


def test_posts_text_payload_when_configured(monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/test")

    def fake_post(url, json=None, timeout=None):
        assert url == "https://hooks.slack.com/services/test"
        return httpx.Client(transport=httpx.MockTransport(_mock_handler)).post(
            "https://hooks.slack.com/services/test", json=json
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    notify_slack("[URGENT] Ticket GOR-1 flagged")

    assert posted == [{"text": "[URGENT] Ticket GOR-1 flagged"}]
