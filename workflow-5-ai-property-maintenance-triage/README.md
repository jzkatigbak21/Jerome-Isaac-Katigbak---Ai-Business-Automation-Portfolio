# Workflow 5: AI Property Maintenance Triage & Dispatch

An AI-powered maintenance triage and dispatch system for property
management, built on **Make.com + Airtable**, with the **Claude API**
doing the actual classification. Same core pattern as
[Workflow 4](../workflow-4-ai-support-ticket-triage/) (classify, flag
what needs a human, close the loop instead of producing a report nobody
checks) -- rebuilt on a low-code stack instead of Python, to demonstrate
the same judgment applies regardless of tooling.

See [`architecture.md`](architecture.md) for design rationale, or keep
reading for the full build below.

## Objective

Take an incoming tenant maintenance request and, for each one:
1. Classify urgency, category, and write a one-sentence summary
2. Flag anything that needs a human before any vendor is contacted
   (safety concerns, low model confidence) instead of auto-dispatching
3. For everything else, automatically match and notify the right vendor
4. Close the loop: write results back where the property manager and
   vendors actually work, not into a report nobody opens

## Workflow

```text
Tenant submits request (public Airtable form)
        v
Make.com: Airtable "Watch Records" trigger
        v
Claude API -- HTTP module, forced tool-use for structured output
  (urgency, category, summary, confidence, needs_human_review)
        v
Airtable "Update a Record" -- classification written back
        v
Airtable "Search Records" -- possible-duplicate check: same property,
  same category, still open, submitted within the last 7 days
        v
Router on duplicate found
  |
  +-- yes --> Status -> Possible Duplicate, PM emailed with both
  |           requests side by side (unit numbers included, so the PM
  |           can tell "same tenant re-reporting" from "two genuinely
  |           separate issues that just share a category")
  |           PM reviews and manually resolves either way:
  |             - genuinely separate  -> assign a vendor as usual,
  |               re-uses the same automation as the Pending Review
  |               recovery path below
  |             - actually a duplicate -> Status -> Closed - Duplicate,
  |               Duplicate Of set to the original ticket (never
  |               deleted -- the submission and the audit trail both
  |               stay on record)
  |
  +-- no  --> Router on Needs Human Review
        |
        +-- true  --> PM emailed, Status -> Pending Review
        |             (PM manually assigns a vendor when ready)
        |             v
        |             Airtable Automation: vendor assigned on a Pending
        |             Review record -> vendor emailed, Status -> Vendor Assigned
        |
        +-- false --> Airtable "Search Records" for an active vendor
                      matching the classified category
              |
              +-- found     --> vendor assigned + emailed,
              |                 Status -> Vendor Assigned
              +-- not found --> Status -> No Vendor Available, PM emailed
        v
Vendor self-reports via a second public form (Scheduled / Completed)
        v
Airtable Automation relays the update onto the original record
        v
Property Manager Dashboard (Airtable Interface): KPIs, Needs My
Attention / In Progress / All Records views, category + property charts
```

## Features

- Structured AI output via forced Claude tool-use, called directly from
  a Make.com HTTP module (no native app connector, full control over
  the request/response shape -- same reliability pattern as Workflow 4)
- Human-in-the-loop safety split: emergencies and low-confidence
  classifications route to a property manager instead of being
  auto-dispatched to a vendor
- Automatic vendor matching by category + active status, with a
  distinct `No Vendor Available` status (not silently dropped) when no
  active vendor covers a category
- Possible-duplicate detection: before dispatching, checks for another
  open request at the same property in the same category submitted in
  the last 7 days -- catches both a tenant re-reporting the same issue
  and different tenants reporting the same building-wide problem,
  without needing an exact-match on unit number. Flags for a human
  rather than auto-merging, since a formula can't tell "shared building
  system failing" from "two coincidentally similar unrelated issues" --
  the notification includes both requests' unit numbers so the property
  manager can make that call in seconds
- Two public-facing self-service forms: tenant intake (creates a new
  request directly) and vendor status updates (relayed via a staging
  table + automation, since Airtable forms can only create records, not
  update existing ones)
- Airtable schema provisioned via API scripts (Python + Airtable's
  Metadata API) instead of manually clicking through field types
- Property Manager Dashboard (Airtable Interface): live KPIs, a
  prioritized "Needs My Attention" queue, an "In Progress" view, and
  category/property breakdown charts
- 150-row synthetic seed dataset (Python-generated, no API calls) for
  testing the dashboard at realistic volume without spending on live
  classification for bulk data

## Setup

Requires an Airtable account (workspace + base) and a Make.com account
(free tier is enough), plus a Claude API key.

```bash
cd workflow-5-ai-property-maintenance-triage
pip install httpx python-dotenv
cp .env.example .env   # fill in AIRTABLE_TOKEN and AIRTABLE_BASE_ID
```

```bash
# Provision the Airtable schema (Properties, Vendors, Maintenance Requests)
python scripts/provision_airtable_base.py

# Add sample vendors, one per specialty
python scripts/seed_vendors.py

# Generate 150 synthetic requests for volume-testing the dashboard
python scripts/generate_seed_requests.py
```

The Make.com scenario, Airtable Automations, and Interface itself are
built in their respective UIs (not something a script can provision) --
see `architecture.md` for the module-by-module breakdown.

## Real bugs hit and fixed while building this

Documenting these because they're the actual substance of the build --
anyone can describe an architecture, fewer people have debugged one:

- **Airtable's schema API rejects computed field types.** `autoNumber`
  and `createdTime` show up in Airtable's own API docs with example
  JSON, but the live API returns `422 UNSUPPORTED_FIELD_TYPE_FOR_CREATE`
  for both -- they're UI-only. Had to add them by hand after
  provisioning the rest via script, and reorder the primary field since
  `autoNumber` isn't a valid primary field via the API either.
- **A table-injection script bug that deleted data.** A dashboard script
  reused for multiple tables searched for the wrong closing brace when
  replacing an existing key's block, silently deleting every table
  after the one being replaced. (This one's actually from Workflow 4's
  dashboard tooling, not this project -- included here because it's the
  same class of "verify the actual diff, don't assume a copy-pasted
  pattern still applies" lesson that came up again below.)
- **Make.com's module reference numbers aren't sequential.** They're
  internal IDs Make.com assigns, not 1/2/3 in scenario order -- caused a
  `references non-existing module` error until corrected to match the
  scenario's actual badge numbers.
- **A stray colon, then stray whitespace, broke the Claude HTTP call
  twice in a row.** First an `Invalid value for header` from typing
  `x-api-key:` (with the colon) into the header Name field instead of
  the separate Value field; then the same error again from whitespace
  picked up in a copy-pasted API key. The second one also **exposed a
  real API key in an error log**, caught and rotated immediately.
- **Airtable's "Find records" condition builder has no Record ID
  filter.** Expected one, wasn't there -- had to match on a different
  unique field instead, or use a nested dynamic-content lookup where
  available (`Assigned Vendor -> Email` worked directly, skipping a
  Find Records step entirely).
- **Airtable's native "Send email" automation action can only email
  base collaborators**, a billing-plan restriction -- discovered by
  actually trying to notify a real external vendor and getting
  `Cannot email non-collaborators`. Fixed by connecting Gmail directly
  as its own integration inside the automation instead of using
  Airtable's built-in email action.
- **A field-naming mismatch would have silently broken vendor
  matching.** The Vendors table's `General` specialty had no matching
  `Category` option (`Other` existed instead) -- any general-handyman
  request would have come back `No Vendor Available` even with an
  active General vendor on file. Caught before it shipped, not after.
- **The vendor notification email told vendors to "reach out to the
  tenant directly" without ever including the tenant's contact info.**
  A real usability gap, not a technical bug -- caught by re-reading the
  template as if actually receiving it.
- **"When a record is updated" doesn't fire on record creation.** A
  form submission that creates a fully-populated record never triggers
  that automation type -- it only watches for changes to *existing*
  records. Silently produced zero executions until switched to "When a
  record is created."
- **A linked-record field compared as text silently never matched,
  with no error.** The possible-duplicate check's formula compared
  `{Property}` against a Make.com token that turned out to be an array
  (`Property[]`), not plain text -- Airtable's API returns link fields
  as arrays of record IDs, always, never the linked record's display
  name. The formula ran without error and just never found a match.
  Confirmed by isolating the condition (temporarily dropping `Property`
  from the formula) and watching it suddenly start finding real
  results -- the cleanest way to prove which specific condition was
  silently failing, rather than guessing.
- **Fixing that array bug the first way created a different one.** Once
  it was confirmed the token was an array, the fix used a "Get a
  Record" module to resolve the linked Property into its actual name --
  except that module was misconfigured to query the wrong table
  (`Maintenance Requests` instead of `Properties`) with the wrong ID
  (the current record's own ID instead of the linked property's ID),
  so it just fetched the same record back again. Two separate
  misconfigurations on one module, both needed fixing before the
  lookup actually worked.
- **Two separate missing-parenthesis errors from hand-editing formula
  text.** Once while isolating the Property condition for testing
  (deleted a condition without its matching paren), once while adding
  a date-range condition (`IS_AFTER(...)` ended up nested inside
  `NOT(...)` instead of alongside it as its own sibling condition to
  `AND(...)`). Airtable's `422 Invalid formula` error doesn't say
  *where* the mismatch is, just that there is one -- both required
  manually counting parens against the actual intent.
- **A multi-match search meant multi-fire everything downstream.**
  When the duplicate check found 4 open requests matching the same
  property and category, every module after it -- the status update,
  the PM email -- fired once *per match*, not once total, which is
  Make.com's default behavior for any module that returns multiple
  bundles. Fixed by setting the Search Records module's own `Limit` to
  1, so at most one match is ever considered regardless of how many
  actually exist.

## Sample results

_Live-tested scenarios, each verified end-to-end through the real
Make.com scenario and Airtable automations:_

| Test case | Classification | Outcome |
|---|---|---|
| "No hot water, can smell gas near the water heater" | Emergency / Plumbing | Routed to PM (`Pending Review`), no vendor auto-dispatched |
| "Kitchen faucet has a slow drip, not urgent" | Routine / Plumbing | Vendor auto-matched, assigned, and emailed |
| "Kitchen cabinet hinge is squeaking" | Routine / Structural | Correctly returned `No Vendor Available` before a Structural vendor existed on file; matched correctly once one was added |
| A second Structural request at a property with an existing open Structural request | Routine / Structural | Correctly flagged `Possible Duplicate` instead of auto-dispatching a second vendor for what might be the same issue |

_Property Manager Dashboard, live snapshot (150 synthetic seed records
plus live-tested ones):_

| Metric | Value |
|---|---|
| Total open requests | 143 |
| Requests needing review | 22 |
| Requests with no vendor available | 7 |
| Completed this week | 25 |
| Completed this month | 25 |

Category and property breakdown charts render live in the dashboard,
letting a property manager spot patterns (e.g. one property generating
disproportionately more plumbing requests) that a flat list wouldn't
surface.

## Key Skills Demonstrated

- Claude API integration from inside a low-code platform (structured
  output via forced tool-use, called through a generic HTTP module)
- Low-code workflow orchestration (Make.com: routing, branching,
  isolated module testing, cached-bundle debugging)
- Airtable schema design and API-driven provisioning (Python + Metadata
  API, distinct from the Data API used for records)
- Human-in-the-loop automation design (safety-net routing, staging-table
  pattern for external-facing update forms)
- Cross-platform integration troubleshooting (Make.com, Airtable
  Automations, Gmail, Claude API) -- diagnosing from actual execution
  logs and error messages, not guessing
- Dashboard/reporting design (Airtable Interfaces)
- Synthetic test data generation (Python) for volume-testing without
  live API cost

## Future Improvements

- SLA countdown timers on Emergency-routed requests
- Vendor performance scorecard (response/completion time per vendor,
  via a rollup field) on the dashboard
- Reply-to-email or SMS status updates as an alternative to the vendor
  form, for vendors who won't reliably click a link
