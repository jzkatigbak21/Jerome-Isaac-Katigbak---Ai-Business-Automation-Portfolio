"""Verifies the --source gorgias skip-already-processed logic in
main() -- mocks every I/O boundary (Gorgias, Claude, run_batch) so this
runs offline and fast, without needing real credentials or network access.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.cli import main
from src.triage.io_utils import Ticket
from src.triage.pipeline import BatchOutcome


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("GORGIAS_SUBDOMAIN", "test-store")
    monkeypatch.setenv("GORGIAS_EMAIL", "agent@example.com")
    monkeypatch.setenv("GORGIAS_API_KEY", "test-key")
    monkeypatch.chdir(tmp_path)  # keep the out/ this run writes contained to a scratch dir


def _tickets() -> list[Ticket]:
    return [
        Ticket("GOR-1", "Jane", "email", "already processed"),
        Ticket("GOR-2", "John", "email", "brand new"),
    ]


def test_gorgias_source_skips_already_processed_tickets(monkeypatch):
    monkeypatch.setattr("sys.argv", ["cli.py", "--source", "gorgias"])

    with patch("src.cli.fetch_tickets", return_value=_tickets()), \
         patch("src.cli.has_ai_triage_note", side_effect=lambda ticket_id: ticket_id == "GOR-1"), \
         patch("src.cli.TriageClient"), \
         patch("src.cli.run_batch", return_value=BatchOutcome(results=[], failures=[])) as mock_run_batch:
        main()

    processed = mock_run_batch.call_args[0][0]
    assert [t.ticket_id for t in processed] == ["GOR-2"]


def test_gorgias_source_force_flag_reprocesses_everything(monkeypatch):
    monkeypatch.setattr("sys.argv", ["cli.py", "--source", "gorgias", "--force"])

    with patch("src.cli.fetch_tickets", return_value=_tickets()), \
         patch("src.cli.has_ai_triage_note") as mock_has_note, \
         patch("src.cli.TriageClient"), \
         patch("src.cli.run_batch", return_value=BatchOutcome(results=[], failures=[])) as mock_run_batch:
        main()

    mock_has_note.assert_not_called()  # --force skips the check entirely, no wasted lookups either
    processed = mock_run_batch.call_args[0][0]
    assert [t.ticket_id for t in processed] == ["GOR-1", "GOR-2"]


def test_csv_source_never_calls_has_ai_triage_note(monkeypatch, tmp_path):
    csv_path = tmp_path / "tickets.csv"
    csv_path.write_text("ticket_id,customer_name,channel,text\nT-1,Jane,email,hello\n")
    monkeypatch.setattr("sys.argv", ["cli.py", "--source", "csv", "--input", str(csv_path)])

    with patch("src.cli.has_ai_triage_note") as mock_has_note, \
         patch("src.cli.TriageClient"), \
         patch("src.cli.run_batch", return_value=BatchOutcome(results=[], failures=[])) as mock_run_batch:
        main()

    mock_has_note.assert_not_called()  # the skip-check only makes sense against a live Gorgias account
    processed = mock_run_batch.call_args[0][0]
    assert [t.ticket_id for t in processed] == ["T-1"]
