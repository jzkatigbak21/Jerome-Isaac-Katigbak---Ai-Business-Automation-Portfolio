# Architecture: AI Support Ticket Triage

## Problem

A DTC brand's support inbox mixes shipping complaints, defective-product
reports, refund requests, five-star praise, and general questions. A human
has to read every single one before anything happens. Most of that volume
is repetitive and low-risk to answer; a small fraction is genuinely
sensitive (safety issues, chargeback threats, angry repeat complaints) and
must never get an automated reply.

## Design decisions

**Forced tool call instead of "return JSON" prompting.** Early iterations
asked the model to reply with raw JSON in the system prompt. That's fragile
at volume -- markdown fences, a stray leading sentence, or a truncated
response all break `json.loads`. Switching to `tool_choice: {"type": "tool", ...}`
(see [`client.py`](src/triage/client.py)) makes the API itself constrain the
response shape, so parsing failures become a rare edge case instead of the
normal failure mode at 300+ rows.

**Defense in depth on the human-review flag.** The model is asked to set
`needs_human_review` itself, but [`pipeline.py`](src/triage/pipeline.py)
also runs a second, independent check: a keyword list for legal/chargeback/
safety language, and a hard confidence floor. Either one can force a flag
the model didn't set; neither can un-flag one the model did set. The
reasoning: a single LLM judgment call is fine for "is this a shipping
question," but not the only thing standing between an angry customer
threatening legal action and an auto-sent reply.

**Bounded concurrency, not a request-per-ticket loop.** A plain `for`
loop over 300 tickets at ~1-2s/request would take 5-10 minutes and offers
no isolation -- one hung request blocks everything behind it. Tickets are
fanned out across a `ThreadPoolExecutor` sized by `MAX_CONCURRENT_REQUESTS`
(default 5, tunable via `.env`), keeping requests-per-minute under typical
tier rate limits while still processing a batch in roughly the time of one
request's latency times `batch_size / max_workers`.

**Retry policy: exponential backoff + jitter, capped attempts, narrow
exception scope.** Only `RateLimitError`, `APITimeoutError`,
`APIConnectionError`, and `InternalServerError` are retried
(`client.py`). A `BadRequestError` (e.g., malformed input) is not retried
-- retrying a request that will deterministically fail again just burns
quota and delays the failure report.

**Failures don't kill the batch.** `run_batch` catches exceptions per
ticket after retries are exhausted, logs them, and continues. A single
persistently-failing ticket produces one row in `failures.csv` for
reprocessing, not a stack trace that stops the other 299.

**One combined call, not classify-then-draft.** Classification and reply
drafting happen in a single request per ticket. Splitting them would double
API cost and latency for the ~85% of tickets that turn out to be
straightforward, for no accuracy benefit -- the model has the full ticket
text in front of it either way.

## Data flow

```text
data/sample_tickets.csv (or a real Gorgias/Shopify export)
        |
        v
io_utils.load_tickets()  -->  list[Ticket]
        |
        v
pipeline.run_batch()
  ThreadPoolExecutor(max_workers=N)
        |
        +--> client.TriageClient.classify()  (forced tool_use, retried on transient errors)
        |         |
        |         v
        |    pipeline._apply_safety_net()  (keyword + confidence override)
        |
        v
  BatchOutcome(results, failures)
        |
        v
io_utils.write_results() / write_failures()
        |
        v
out/results.csv, out/human_review_queue.csv, out/failures.csv
```

## What this does not do (by design, for a portfolio-scoped project)

- No live Shopify/Gorgias API integration -- CSV in, CSV out. Swapping the
  input source only touches `io_utils.load_tickets`.
- No persistent queue/DB -- each run is a stateless batch job.
- No automated sending of drafted replies -- output is a CSV an agent
  reviews before anything goes out, matching the human-in-the-loop pattern
  used across the rest of this portfolio.
