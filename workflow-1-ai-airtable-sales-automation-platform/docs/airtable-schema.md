# Airtable Schema

## Overview

The Airtable base acts as the CRM, approval interface, workflow queue, communication history, and automation log for the outbound sales automation platform.

The base contains four main tables:

```text
Leads
Outreach
Follow-ups
Automation Logs
```

The `Leads` table is the central table. The other tables link back to it using Airtable linked-record fields.

---

# Table Relationships

```text
Leads
 ├── Outreach
 ├── Follow-ups
 └── Automation Logs
```

A single lead can have:

- Multiple outreach records
- Multiple follow-up records
- Multiple automation log records

---

# Leads Table

## Purpose

Stores lead information, AI-generated research, outreach drafts, approval status, delivery state, and follow-up scheduling.

| Field | Airtable Field Type | Description |
|---|---|---|
| LeadID | Autonumber | Unique internal lead number |
| Lead Name | Formula | Human-readable lead label |
| Company Name | Single line text | Company associated with the lead |
| Company Website | URL | Company website used for research |
| Contact First Name | Single line text | Prospect first name |
| Contact Last Name | Single line text | Prospect last name |
| Job Title | Single line text | Prospect role |
| Email Address | Email | Outreach recipient |
| LinkedIn URL | URL | Prospect LinkedIn profile |
| Industry | Single select | AI-classified primary industry |
| Company Location | Single line text | Company location |
| Submitted By | Single line text | Person who submitted the lead |
| Submission Date | Created time | Date the lead was added |
| Automation Status | Single select | Current workflow stage |
| Research Summary | Long text | AI-generated company summary |
| Pain Points | Long text | Likely business pain points |
| Personalization Angle | Long text | Suggested outreach angle |
| Email Subject | Single line text | AI-generated outreach subject |
| Email Draft | Long text | AI-generated initial email |
| Approval Status | Single select | Human approval state |
| Sent Status | Single select | Email delivery state |
| Sent Date | Date with time | Date the initial email was sent |
| Next Follow-Up | Date with time | Scheduled follow-up date |
| Error Message | Long text | Workflow error details |
| Outreach | Link to another record | Related Outreach records |
| Follow-ups | Link to another record | Related Follow-up records |
| Automation Logs | Link to another record | Related log records |

## Lead Name Formula

```text
"Lead " & {LeadID} & " - " & {Company Name}
```

Example:

```text
Lead 6 - Gymshark
```

## Automation Status Options

```text
New
Processing
Researching
Drafting
Awaiting Review
Approved
Sending
Completed
Failed
```

## Approval Status Options

```text
Pending Review
Approved
Rejected
Needs Revision
```

## Sent Status Options

```text
Not Sent
Scheduled
Sent
Replied
Bounced
```

## Industry Options

```text
SaaS
Software
Ecommerce
Retail
Healthcare
Finance
Manufacturing
Other
```

---

# Outreach Table

## Purpose

Stores a permanent history of all initial outreach and follow-up emails sent by the system.

| Field | Airtable Field Type | Description |
|---|---|---|
| Outreach ID | Autonumber | Unique outreach record number |
| Related Lead | Link to another record → Leads | Lead associated with the email |
| Outreach Type | Single select | Initial email or follow-up type |
| Email Subject | Single line text | Sent email subject |
| Email Body | Long text | Sent email content |
| Status | Single select | Delivery status |
| Created Date | Created time or Date with time | Date the record was created |
| Scheduled Send Date | Date with time | Planned send date |
| Sent Date | Date with time | Actual send date |
| Recipient Email | Email | Email recipient |
| Reply Status | Single select | Reply tracking state |

## Outreach Type Options

```text
Initial Outreach
Follow-up 1
Follow-up 2
Follow-up 3
```

## Status Options

```text
Draft
Scheduled
Sent
Failed
```

## Reply Status Options

```text
No Reply
Replied
Interested
Not Interested
Bounced
```

---

# Follow-ups Table

## Purpose

Stores scheduled follow-up tasks, AI-generated drafts, approval state, and send history.

| Field | Airtable Field Type | Description |
|---|---|---|
| Follow-up ID | Autonumber | Unique follow-up record number |
| Related Lead | Link to another record → Leads | Lead associated with the follow-up |
| Follow-Up Number | Number | Sequence number of the follow-up |
| Due Date | Date with time | Date the follow-up becomes eligible for generation |
| Subject | Single line text | AI-generated follow-up subject |
| Draft | Long text | AI-generated follow-up email |
| Status | Single select | Follow-up workflow state |
| Sent Date | Date with time | Date the follow-up was sent |
| Created at | Created time | Date the record was created |
| Email Address | Email or Lookup | Recipient email from the related lead |

## Status Options

```text
Scheduled
Awaiting Review
Approved
Rejected
Sent
Failed
```

---

# Automation Logs Table

## Purpose

Creates an audit trail of workflow activity and links each event to the related lead.

| Field | Airtable Field Type | Description |
|---|---|---|
| Timestamp | Created time | Time the log record was created |
| Workflow | Single select | Workflow that generated the log |
| Relate Lead | Link to another record → Leads | Lead associated with the event |
| Status | Single select | Workflow outcome |
| Message | Long text | Description of the event or error |

## Workflow Options

```text
Lead Intake
Company Research
Outreach Generation
Human Approval
Email Sender
Follow-up Generator
Follow-up Approval
Send Follow-up
Dashboard Update
```

## Status Options

```text
Started
Success
Warning
Failed
Skipped
```

---

# Recommended Airtable Views

## Leads Views

```text
New Leads
Processing
Drafting
Awaiting Review
Approved Leads
Sent Outreach
Failed Automations
```

Example filters:

```text
New Leads:
Automation Status = New

Awaiting Review:
Automation Status = Awaiting Review

Approved Leads:
Approval Status = Approved
AND Sent Status = Not Sent

Sent Outreach:
Sent Status = Sent

Failed Automations:
Automation Status = Failed
```

## Follow-up Views

```text
Scheduled Follow-ups
Awaiting Review
Approved Follow-ups
Sent Follow-ups
Failed Follow-ups
```

## Outreach Views

```text
All Outreach
Initial Emails
Follow-ups
Sent Emails
Failed Emails
```

## Automation Log Views

```text
All Logs
Success
Warnings
Failures
By Workflow
```

---

# Airtable Interface Pages

The Airtable Interface provides a user-friendly layer for monitoring and approvals.

```text
Dashboard Landing Page
Analytics
Sent Emails
Review Lead Drafts
Review Follow-up Drafts
```

## Dashboard Landing Page

Displays:

- New Leads
- Drafting
- Pending Review
- Sent Today
- Failed Leads
- Pending Follow-ups
- Recent Activity Feed

## Analytics

Displays:

- Research Completed Leads
- Total Emails Sent
- Approval Rate
- Automation Success Rate
- Leads by Industry

## Sent Emails

Displays:

- Company Name
- Contact First Name
- Contact Last Name
- Sent Date
- Email Subject
- Sent Status

## Review Lead Drafts

Allows reviewers to inspect and edit:

- Research Summary
- Pain Points
- Personalization Angle
- Email Subject
- Email Draft
- Approval Status

## Review Follow-up Drafts

Allows reviewers to inspect and edit:

- Related Lead
- Follow-Up Number
- Due Date
- Subject
- Draft
- Status

---

# Data Integrity Rules

- `LeadID`, `Outreach ID`, and `Follow-up ID` are computed fields and should not be updated by n8n.
- Linked-record fields must be populated using Airtable record IDs.
- Linked-record values must be sent as arrays.

Example:

```javascript
{{ [$json.id] }}
```

- n8n should update records using the Airtable `id` field rather than the visible autonumber.
- Single-select values generated by AI must exactly match the available Airtable options.
- Sender workflows should validate recipient, subject, body, approval state, and send status before delivery.

---

# Workflow State Summary

## Lead Lifecycle

```text
New
→ Processing
→ Drafting
→ Awaiting Review
→ Sending
→ Completed
```

Failure path:

```text
Any active state
→ Failed
```

## Follow-up Lifecycle

```text
Scheduled
→ Awaiting Review
→ Approved
→ Sent
```

Failure path:

```text
Scheduled / Approved
→ Failed
```
