# Workflow 4: AI Support Ticket Triage

A batch tool that classifies support tickets/reviews (sentiment, urgency,
category, extracted entities), drafts ready-to-send replies for
straightforward cases, and flags anything sensitive for a human -- with a
hedged starting-point draft even on the flagged ones, so a human never
starts from a blank page -- built directly against the **Claude API**
with Claude Code, no low-code automation platform in the pipeline itself.

Unlike the other workflows in this portfolio (n8n/Airtable/Zapier
orchestration), this project is the pipeline: real Python, its own retry
and concurrency handling, and its own test suite. n8n/Airtable/CRM tools
are a natural next step as the *output destination* (push
`human_review_queue.csv` into Airtable or Gorgias), not the engine.

Three ways to feed it tickets, in increasing order of "how this would
actually run in production": a CSV batch, a polling pull from a live
Gorgias account (`--source gorgias`), or a real-time webhook receiver
(`src/webhook_server.py`) that Gorgias calls the instant a ticket is
created. See "Real-time webhook" below for why polling isn't the final
shape for live triage.

See [`architecture.md`](architecture.md) for the design rationale.

## Objective

Take a batch of customer support tickets or product reviews and, for each
one:
1. Classify sentiment, urgency, and category
2. Extract order number and product name
3. Draft a send-ready reply for the straightforward, low-risk cases
4. Flag anything that needs a human (legal/safety language, low
   confidence, account/payment changes, repeat escalations) instead of
   guessing -- but still draft a hedged starting-point reply where
   possible, rather than leaving the agent with nothing but a reason

## Pipeline

```text
CSV of tickets, a poll of Gorgias (--source gorgias), or a live webhook
(src/webhook_server.py) -- all three converge on process_one()
        v
Batch path fans out across a bounded ThreadPoolExecutor;
the webhook path calls process_one() directly, per ticket, in real time
        v
Claude API -- forced tool_use call per ticket
  (classify + draft reply in one request)
        v
Retry w/ exponential backoff + jitter on 429 / timeout / 5xx
        v
Safety-net override (keyword + confidence floor)
        v
out/results.csv (batch) or out/live_results.csv (webhook)
```

## Features

- Structured output via forced Claude tool-use (no brittle "please return JSON" parsing)
- Exponential backoff + jitter retries on rate limits, timeouts, and 5xx errors
- Bounded concurrency batch processing, tested against 300 synthetic tickets
- Keyword + confidence-floor safety net that can force a human-review flag even if the model didn't set one
- Flagged tickets still get a draft where possible -- a hedged starting point (acknowledge + hold, no promised refunds/replacements, no responding to legal/chargeback claims directly) rather than nothing, distinct from the ready-to-send draft on non-flagged tickets
- Per-ticket failure isolation -- one bad ticket can't take down the batch
- Live Gorgias integration (`--source gorgias`) alongside the CSV path -- pulls real tickets via the Gorgias REST API and maps them into the same pipeline, tested against a real Shopify dev store + Gorgias trial
- Real-time webhook receiver (`src/webhook_server.py`) -- classifies a ticket the instant Gorgias creates it, instead of waiting for the next poll
- Offline unit test suite (retry logic, safety-net logic, batch failure isolation, Gorgias mapping, webhook payload handling) -- no live API calls needed to verify correctness

## Setup

```bash
cd workflow-4-ai-support-ticket-triage
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY (and GORGIAS_* if using --source gorgias)
```

## Usage

```bash
# Generate a fresh synthetic dataset (optional, one is already in data/)
python scripts/generate_sample_data.py --rows 300 --out data/sample_tickets.csv

# Cheap smoke test on the first 20 tickets before spending on a full run
python -m src.cli --input data/sample_tickets.csv --out-dir out --limit 20 --verbose

# Run the full batch triage
python -m src.cli --input data/sample_tickets.csv --out-dir out --verbose

# Or pull real tickets from a connected Gorgias account instead of a CSV
python -m src.cli --source gorgias --out-dir out --verbose

# --source gorgias skips tickets that already have an [AI Triage] note
# (from a prior run, the webhook, or the backfill script) -- makes this
# usable as a cron-scheduled polling alternative to the webhook, since
# each run only costs a Claude call for genuinely new tickets. Pass
# --force to reprocess everything anyway (e.g. while tuning prompts
# against the same known tickets).
python -m src.cli --source gorgias --out-dir out --force --verbose
```

Output lands in `out/`:
- `results.csv` -- every ticket with its classification and draft reply
- `human_review_queue.csv` -- the subset flagged for a human
- `failures.csv` -- tickets that failed after retries were exhausted (if any)

## Real-time webhook (optional)

`--source gorgias` polls -- it pulls whatever tickets exist *right now*.
That's fine for batch/backfill, but a real support team needs a reply
drafted within seconds of a ticket arriving, not whenever the next poll
happens to run. `src/webhook_server.py` is the production-shape
alternative: a small FastAPI receiver that Gorgias calls the instant a
ticket is created, classifying that one ticket in real time instead of
waiting for a batch.

```bash
# 1. Run the receiver locally
uvicorn src.webhook_server:app --reload --port 8000

# 2. Expose it to the internet (Gorgias is a live SaaS, it can't reach localhost)
ngrok http 8000
```

Then in Gorgias, go to **Settings -> HTTP integration** (not the Rules/
Automations action list -- outbound webhooks live in their own settings
page) and enable it for the **Ticket created** event: URL
`https://<your-ngrok-id>.ngrok-free.app/webhook/gorgias`, method `POST`,
content type `application/json`, and a JSON body of
`{"ticket_id": "{{ticket.id}}"}` (Gorgias pre-fills this exact template).
The receiver defensively accepts a few common payload shapes (`ticket_id`,
`id`, `ticket.id`, `data.id`) in case that default ever changes. Add a
header `ngrok-skip-browser-warning: true` to skip ngrok's free-tier
interstitial page, and set `WEBHOOK_SECRET` in `.env` (plus a matching
`X-Webhook-Secret` header in Gorgias) to require a shared secret on
incoming requests -- otherwise the endpoint accepts unauthenticated
requests, fine for a local demo, not for anything exposed longer-term.

**Verified live end-to-end:** with the receiver running and a Gorgias HTTP
integration pointed at it, creating a ticket in Gorgias triggered the full
chain -- webhook fired, ticket + messages fetched from the Gorgias API,
classified by Claude, and logged -- in about 5 seconds with no polling:

```
Ticket GOR-74619543 (Francesca Thea Isabella Mejos) -> flagged for review [other/high]
INFO:     34.6.16.210:0 - "POST /webhook/gorgias HTTP/1.1" 200 OK
```

**Closing the loop:** the receiver also writes the result back onto the
ticket as a Gorgias internal note (`POST /tickets/{id}/messages`) -- an
agent opens the ticket and sees "[AI Triage] category=... urgency=..."
plus the drafted reply, right where they already work, instead of
needing to go check a CSV. Flagged tickets never lose the warning just
because a draft is also present: the note always leads with "FLAGGED FOR
HUMAN REVIEW" and the reason first, with the draft appended underneath
labeled "Suggested starting point (needs review, not ready to send)" --
a deliberately different label from the ready-to-send draft on
non-flagged tickets, so nobody mistakes a starting point for something
safe to fire off as-is. A note-write failure is logged but never breaks
the webhook response -- the classification is already saved regardless.

The safety-net keyword override (until this point only exercised by unit
tests) also fired correctly against a real ticket: a live email
mentioning an allergic reaction to a product got flagged for human
review -- the same behavior `pipeline.py`'s `ESCALATION_KEYWORDS` check
was written to guarantee, now confirmed end-to-end, not just in mocks.

**Making flagged tickets visible, not just flagged:** a note nobody's
looking for does nothing. Every flagged ticket gets tagged `ai-flagged`
(merged into its existing tags via `update_ticket_flags()`, never
clobbering what other automations already set) so it surfaces in a saved
Gorgias view. The genuinely urgent ones -- high urgency *and* flagged,
the chargeback-threat ticket is the textbook case -- additionally get
their priority bumped to `high` and an optional Slack ping
(`SLACK_WEBHOOK_URL`, a no-op if unset) instead of relying on someone
happening to check that view.

**Verified live:** a real chargeback-threat test ticket sent through the
webhook came out flagged `other/high`, got its Gorgias priority bumped to
`high`, and posted a Slack message to the configured channel within
seconds -- no polling, no manual queue-checking.

Tickets that predate the webhook (created via the CSV/`--source gorgias`
path, or before this code existed) never got a note, tag, priority bump,
or Slack ping -- the webhook only fires on the one-time "ticket created"
event, so it can't retroactively touch old tickets. `scripts/backfill_notes.py`
covers that gap: it re-fetches existing tickets, classifies each, and
applies the exact same `format_triage_note()` / `surface_flagged_ticket()`
treatment the webhook would have -- both paths share the same functions,
so old and new tickets end up identically handled.

Safe to re-run: `has_ai_triage_note()` checks each ticket's thread for a
prior `[AI Triage]` note *before* classifying, so a ticket already
processed (by an earlier backfill run, or by the webhook) is skipped
entirely -- no duplicate note, and no wasted Claude call, since the check
happens before the classification step, not after.

```bash
python scripts/backfill_notes.py
```

**Idempotency:** webhooks are at-least-once, not exactly-once -- if Gorgias
doesn't get a 2xx back fast enough, it retries the same delivery, which
would otherwise reclassify (and double-bill Claude for) a ticket already
handled. The receiver dedupes on `ticket_id` against `live_results.csv`
before doing any of the expensive work, so a retried delivery is a no-op.

Each processed ticket lands in `out/live_results.csv`.

**From local dev to production:** `uvicorn` in a terminal plus `ngrok` is
strictly a dev/testing setup -- it depends on a laptop staying awake and
a tunnel URL that changes every restart, and Gorgias needs a stable
HTTPS endpoint that's actually up when a ticket arrives at 3am. A real
DTC brand would deploy this as either an always-on container (Railway,
Render, Fly.io -- push the code, get a permanent HTTPS domain, automatic
restarts, secrets managed in a dashboard instead of a local `.env`) or as
a serverless function (AWS Lambda via `Mangum`, Cloud Run, Vercel --
a natural fit since a webhook receiver is spiky and stateless: no
ticket, no invocation, no cost). Either path also swaps the `print`/log
statements here for something like CloudWatch, Datadog, or Sentry, since
nobody's watching a terminal window when the pager-worthy ticket comes in.

## Tests

```bash
python -m pytest tests/ -v
```

All API calls are mocked, so the suite runs offline and covers: retry-then-succeed,
exhausting retries on persistent rate limiting, not retrying non-retryable errors,
the safety-net override logic, and failure isolation across a batch.

## Sample results

_Live run against the first 20 tickets of the synthetic dataset
(`--limit 20`), via `claude-sonnet-5`:_

| Metric | Value |
|---|---|
| Tickets processed | 20/20 |
| Auto-drafted replies | 12 |
| Flagged for human review | 8 |
| Failures after retries | 0 |

Category breakdown: shipping=5, account=4, praise=4, defect=3, refund=2, other=1, question=1.

_Full 300-row batch, no `--limit`, via `claude-sonnet-5`:_

| Metric | Value |
|---|---|
| Tickets processed | 300/300 |
| Auto-drafted replies | 195 |
| Flagged for human review | 105 |
| Failures after retries | 0 |

Category breakdown: shipping=65, defect=63, praise=59, account=46, refund=39, other=15, question=13.

Same behavior as the 20-row smoke test, just at volume -- see
[`architecture.md`](architecture.md) for how the pipeline handles that
volume (bounded concurrency, retries, failure isolation). Estimated
cost for a run this size is roughly $1-3 on `claude-sonnet-5` pricing --
cheap enough to smoke-test with `--limit` first and run the full batch
without worrying about it.

### Live run against a real Gorgias account

To validate `--source gorgias` end-to-end, not just against mock data, I
connected a free Shopify Partner development store to a Gorgias trial
workspace and seeded it with real inbound tickets (some through Gorgias's
own compose UI, some as genuine inbound emails to the workspace's support
address) referencing real Shopify order numbers.

| Metric | Value |
|---|---|
| Tickets processed | 6/6 |
| Auto-drafted replies | 2 |
| Flagged for human review | 4 |
| Failures after retries | 0 |

Category breakdown: other=2, account=1, defect=1, praise=1, question=1.

Two results worth calling out:
- The escalation ticket (repeat complaint + chargeback threat) was correctly
  flagged high-urgency with no draft attempted -- the safety net working
  against a real, unscripted ticket.
- Gorgias auto-generates an onboarding/welcome message when a workspace is
  created. The pipeline correctly recognized it wasn't a real customer
  inquiry and flagged it for a human to dismiss, rather than hallucinating
  a customer-service reply to a system message.

**[dashboard.html](dashboard.html)** renders all three runs as an
interactive console with a tab toggle -- the 20-row smoke test, the full
300-row batch, and this live Gorgias run -- click through each ticket to
see the original message and Claude's classification. Non-flagged
tickets show a green "ready to send" draft; flagged tickets show the
red review reason plus, where the model had enough to work with, an
amber "suggested starting point -- not ready to send" draft underneath,
visually distinct so the two are never confused.

## Key Skills Demonstrated

- Claude API integration (structured output via tool use)
- Rate limit / retry / error handling
- Concurrent batch processing at volume
- Prompt design for consistent structured output
- Defensive engineering (safety-net overrides, failure isolation)
- Automated testing with mocked external dependencies
- Built end-to-end with Claude Code

## Future Improvements

- Push `human_review_queue.csv` into Airtable for the human-in-the-loop review step (tying this back into the rest of the portfolio's pattern)
- Async I/O (`asyncio` + `AsyncAnthropic`) instead of threads for higher throughput
- Structured logging/metrics export instead of console summary
