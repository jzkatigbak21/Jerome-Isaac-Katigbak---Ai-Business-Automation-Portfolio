# Workflow 4: AI Support Ticket Triage

A batch tool that classifies support tickets/reviews (sentiment, urgency,
category, extracted entities), drafts ready-to-send replies for
straightforward cases, and flags anything sensitive for a human -- built
directly against the **Claude API** with Claude Code, no low-code
automation platform in the pipeline itself.

Unlike the other workflows in this portfolio (n8n/Airtable/Zapier
orchestration), this project is the pipeline: real Python, its own retry
and concurrency handling, and its own test suite. n8n/Airtable/CRM tools
are a natural next step as the *output destination* (push
`human_review_queue.csv` into Airtable or Gorgias), not the engine.

See [`architecture.md`](architecture.md) for the design rationale.

## Objective

Take a batch of customer support tickets or product reviews and, for each
one:
1. Classify sentiment, urgency, and category
2. Extract order number and product name
3. Draft a send-ready reply for the straightforward, low-risk cases
4. Flag anything that needs a human (legal/safety language, low
   confidence, account/payment changes, repeat escalations) instead of
   guessing

## Pipeline

```text
CSV of tickets (or Shopify/Gorgias export)
        v
Bounded-concurrency batch dispatch (ThreadPoolExecutor)
        v
Claude API -- forced tool_use call per ticket
  (classify + draft reply in one request)
        v
Retry w/ exponential backoff + jitter on 429 / timeout / 5xx
        v
Safety-net override (keyword + confidence floor)
        v
out/results.csv, out/human_review_queue.csv, out/failures.csv
```

## Features

- Structured output via forced Claude tool-use (no brittle "please return JSON" parsing)
- Exponential backoff + jitter retries on rate limits, timeouts, and 5xx errors
- Bounded concurrency batch processing, tested against 300 synthetic tickets
- Keyword + confidence-floor safety net that can force a human-review flag even if the model didn't set one
- Per-ticket failure isolation -- one bad ticket can't take down the batch
- Offline unit test suite (retry logic, safety-net logic, batch failure isolation) -- no live API calls needed to verify correctness

## Setup

```bash
cd workflow-4-ai-support-ticket-triage
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

## Usage

```bash
# Generate a fresh synthetic dataset (optional, one is already in data/)
python scripts/generate_sample_data.py --rows 300 --out data/sample_tickets.csv

# Cheap smoke test on the first 20 tickets before spending on a full run
python -m src.cli --input data/sample_tickets.csv --out-dir out --limit 20 --verbose

# Run the full batch triage
python -m src.cli --input data/sample_tickets.csv --out-dir out --verbose
```

Output lands in `out/`:
- `results.csv` -- every ticket with its classification and draft reply
- `human_review_queue.csv` -- the subset flagged for a human
- `failures.csv` -- tickets that failed after retries were exhausted (if any)

## Tests

```bash
python -m pytest tests/ -v
```

All API calls are mocked, so the suite runs offline and covers: retry-then-succeed,
exhausting retries on persistent rate limiting, not retrying non-retryable errors,
the safety-net override logic, and failure isolation across a batch.

## Sample results

_Run against the 300-row synthetic dataset in `data/sample_tickets.csv`:_

| Metric | Value |
|---|---|
| Tickets processed | pending live run |
| Auto-drafted replies | pending live run |
| Flagged for human review | pending live run |
| Failures after retries | pending live run |

(Numbers will be filled in from an actual run once an API key is
configured -- see [`architecture.md`](architecture.md) for how the
pipeline behaves under load in the meantime.)

## Key Skills Demonstrated

- Claude API integration (structured output via tool use)
- Rate limit / retry / error handling
- Concurrent batch processing at volume
- Prompt design for consistent structured output
- Defensive engineering (safety-net overrides, failure isolation)
- Automated testing with mocked external dependencies
- Built end-to-end with Claude Code

## Future Improvements

- Replace CSV I/O with a live Gorgias/Shopify export pull
- Push `human_review_queue.csv` into Airtable for the human-in-the-loop review step (tying this back into the rest of the portfolio's pattern)
- Async I/O (`asyncio` + `AsyncAnthropic`) instead of threads for higher throughput
- Structured logging/metrics export instead of console summary
