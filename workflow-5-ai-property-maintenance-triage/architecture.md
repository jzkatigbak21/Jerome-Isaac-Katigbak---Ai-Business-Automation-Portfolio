# Architecture: AI Property Maintenance Triage & Dispatch

Design rationale -- the *why* behind the choices in
[`README.md`](README.md), which covers the *what*.

## Why Make.com + Airtable instead of Python (like Workflow 4)?

Not a technical limitation -- a deliberate choice to demonstrate the
same judgment on a different stack. Workflow 4 proves the pattern works
end-to-end in code with full control (retries, idempotency, tests).
Workflow 5 proves the same architectural thinking -- classify, flag
what needs a human, close the loop -- holds up when built on the
low-code tools most small teams and agencies actually run on day to
day. The recruiter context this was built for specifically named
Make.com and Airtable as their stack; matching that wasn't incidental.

## Why call Claude via a raw HTTP module instead of Make.com's native app?

Make.com has a native Anthropic/Claude connector, but its support for
*forced* tool-use (guaranteeing structured JSON back, not just a
freeform completion) wasn't something to assume without verifying. A
generic HTTP module calling `api.anthropic.com/v1/messages` directly,
with an explicit `tool_choice`, gives the exact same reliability
guarantee Workflow 4's Python client gets from the SDK -- full control
over the request shape, no dependency on a connector's feature parity
keeping up with the API.

## Why Needs Human Review as the routing signal, not Urgency directly?

`Urgency` (Emergency/Urgent/Routine) and `Needs Human Review` (boolean)
are set together by the same classification call, but they answer
different questions: Urgency describes the ticket, Needs Human Review
decides what the *system* does with it. Keeping them separate means the
router only ever has one boolean to branch on, and the safety logic
(when should this NOT be auto-dispatched) lives in one place in the
prompt rather than being re-derived from urgency strings at every
downstream step.

## Why does Needs Human Review never get overwritten after the fact?

It's the model's classification-time judgment call, kept as a stable
historical record -- not a live "is this still open" flag. `Status`
already tracks the live state (`Pending Review` → `Vendor Assigned` →
`Scheduled` → `Completed`). Any "what needs my attention" view is built
on `Status`, not on `Needs Human Review`, so the two fields each mean
one thing instead of one field trying to do both jobs. Same principle
as Workflow 4, where `needs_human_review` is never mutated once a
ticket's been handled.

## Why a staging table for vendor status updates instead of a form on Maintenance Requests directly?

Airtable forms can only **create** records, never update an existing
one. A vendor form built directly on `Maintenance Requests` would
create a duplicate row per status update instead of updating the real
one. The `Vendor Status Updates` table exists purely to receive the
form submission; a small Automation then finds the matching
`Maintenance Requests` record by `Request ID` and relays the update.
The workaround is the point -- it's the standard pattern for "external
party needs to update one specific existing record without an Airtable
account."

## Why Airtable-native Automations for some steps, Make.com for others?

Whichever tool fits the trigger shape better, not tool loyalty:

- **Make.com** owns the AI-classification path (Airtable trigger →
  Claude → router → vendor match) because it needs an HTTP call to an
  external API mid-flow, which is Make.com's whole reason for existing
  here.
- **Airtable Automations** own the two "when a field changes on an
  existing record" triggers (PM manually assigns a vendor; a vendor's
  form submission needs relaying) because those are simple,
  self-contained "if X, do Y" rules with no external API involved --
  adding a second Make.com scenario just to watch for a field update
  would mean a Last Modified Time field and careful filtering to avoid
  the automation re-triggering on its own writes, for no real benefit
  over Airtable's native trigger built for exactly this.

## Why does the vendor notification email use Gmail directly instead of Airtable's built-in "Send email" action?

Discovered live, not assumed: Airtable's native "Send email" automation
action can only email people who are already collaborators on the
base, a billing-plan restriction -- it can't reach an external vendor's
business email at all. Connecting Gmail as its own integration inside
the automation sends through a real Gmail account instead, with no such
restriction. Found by actually testing against a real external address
and reading the resulting error, not by reading documentation in
advance.

## Why generate synthetic seed data with a script instead of running 150 requests through Claude?

The dashboard needed realistic volume to actually demonstrate the KPIs
and charts meaningfully -- 6 live-tested records don't show a category
breakdown chart doing anything interesting. Generating 150 rows with
already-"classified" fields via a Python script (no API calls) gets
that volume without spending on 150 real classification calls for data
that only needs to *look* like real output, not be independently
verified output. The handful of live-tested cases in the README's
Sample Results table are the ones that actually prove the classification
pipeline works; the 150 synthetic rows exist to prove the dashboard
works at scale.
