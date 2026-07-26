<img width="1693" height="929" alt="repository banner-1" src="https://github.com/user-attachments/assets/763a3998-2480-4ded-99b9-9b1a3fbe5305" />

# AI Business Automation Portfolio

## Overview

This repository showcases four production-style AI automation projects covering business development, outbound sales, proposal generation, and support ticket triage. Each project demonstrates how AI, workflow automation, APIs, and business applications can be combined to solve real operational problems.

The portfolio focuses on practical implementations using **n8n**, **Airtable**, **OpenAI**, **Zapier**, and modern APIs with an emphasis on modular workflow design and human-in-the-loop automation. Workflow 4 is built differently on purpose: no low-code platform in the pipeline, just Python and the **Claude API** directly, with its own retry/concurrency handling and test suite -- built end-to-end with **Claude Code**.

---

## 🎥 Portfolio Walkthrough

https://drive.google.com/file/d/1fF5a4NLAII7zrC4AENpJL3Msu7EMgk1A/view?usp=drive_link
---

# Workflow 4: AI Support Ticket Triage

## Objective

Classify support tickets (sentiment, urgency, category, entities), draft
ready-to-send replies for straightforward cases, and flag anything
sensitive for a human -- with a hedged starting-point draft even on the
flagged ones, so a human is never handed a blank page -- built directly
against the **Claude API** with Claude Code, no low-code automation
platform in the pipeline. Unlike
Workflows 1-3, this project *is* the automation: real Python, its own
retry/concurrency handling, a live third-party API integration, and its
own test suite.

## Workflow

```text
CSV batch, a poll of a live Gorgias account, or a real-time webhook
(Gorgias fires the instant a ticket is created) -- all three converge
on one classification path
        ↓
Claude API
(Forced tool_use: classify + draft reply in one call)
        ↓
Retry with Backoff
(Exponential backoff + jitter on 429 / timeout / 5xx)
        ↓
Safety-Net Override
(Keyword + confidence-floor check forces human review)
        ↓
Written back to Gorgias as an internal note; flagged tickets get
tagged, priority-bumped, and Slack-pinged if urgent
        ↓
CSV Output + interactive dashboard
```

## Features

- Structured output via forced Claude tool-use (no brittle JSON parsing)
- Exponential backoff + jitter retries on rate limits, timeouts, 5xx errors
- Bounded concurrency batch processing, verified at 300-ticket volume
- Keyword + confidence-floor safety net independent of the model's own judgment
- Flagged tickets still get a hedged starting-point draft where possible, not just a bare reason -- visually and textually distinct from the ready-to-send draft on non-flagged tickets so the two can't be confused
- Live Gorgias REST API integration -- both a polling mode (`--source gorgias`) and a real-time webhook receiver, tested against a real Shopify dev store + Gorgias trial account
- Closes the human-in-the-loop: classification results are written back onto the Gorgias ticket as an internal note, flagged tickets are tagged and priority-bumped, and genuinely urgent ones trigger a Slack ping
- Idempotent by design at every entry point (webhook retry-safe dedup, backfill script, CLI `--force` override)
- Interactive HTML dashboard across three real datasets (300-row synthetic batch, 20-row smoke test, live Gorgias tickets)
- Offline unit test suite (40 tests) covering retry logic, safety-net logic, Gorgias mapping, webhook handling, and batch failure isolation

## Business Impact

- Cuts manual triage time on repetitive tickets
- Keeps sensitive/risky tickets in front of a human before anything is sent, with the genuinely urgent ones actively pushed to a team lead instead of waiting to be noticed
- Classifies tickets in real time as they arrive, not just on a batch schedule

## Key Skills Demonstrated

- Claude API Integration (structured output, forced tool use)
- Rate Limit / Retry / Error Handling
- Live Third-Party REST API Integration (Gorgias)
- Real-Time, Event-Driven Architecture (webhook receiver)
- Idempotent System Design
- Concurrent Batch Processing
- Human-in-the-Loop Automation
- Defensive Engineering
- Automated Testing
- Built with Claude Code

---

# Workflow 1: AI Airtable Sales Automation Platform

## Objective

Automate the outbound sales process from lead intake through AI-powered company research, personalized outreach generation, human approval, email delivery, follow-up generation, and outreach tracking.

## Workflow

```text
Airtable Form
(Lead Submission)
        ↓
Lead Intake
(Validate Lead & Queue Processing)
        ↓
Company Research
(Website Research & AI Analysis)
        ↓
AI Outreach Generation
(Create Personalized Email)
        ↓
Human Approval
(Review & Approve Draft)
        ↓
Email Sender
(Send Gmail Outreach)
        ↓
Follow-up Generator
(Create AI Follow-up Draft)
        ↓
Follow-up Approval
(Review & Approve Follow-up)
        ↓
Send Follow-up
(Deliver Follow-up Email)
```

## Features

- AI company research
- Personalized outreach generation
- Human approval workflow
- Gmail automation
- AI-generated follow-ups
- Airtable CRM
- Airtable Interface dashboards
- Automation logging
- Modular 8-workflow architecture

## Business Impact

- Reduces manual prospect research
- Standardizes outreach
- Maintains human review
- Automates follow-up management
- Improves sales visibility

## Key Skills Demonstrated

- n8n
- Airtable
- OpenAI
- Human-in-the-Loop Systems
- Workflow Orchestration

---

# Workflow 2: AI Business Development

## Objective

Identify qualified prospects from an ICP, enrich business information, store contacts in Pipedrive, and generate personalized Gmail drafts.

## Workflow

```text
Google Drive Trigger
(File Updated)
        ↓
Google Docs
(Read ICP)
        ↓
Business Development Manager AI Agent
(Orchestrate Prospecting Workflow)
        ↓
Prospecting Sub-agent
(Search & Qualify Leads)
        ↓
RevOps Sub-agent
(Store Prospects in Pipedrive)
        ↓
SDR Sub-agent
(Generate Personalized HTML Emails)
        ↓
Gmail
(Create Draft Emails)
        ↓
Notification
```


## Features

- Multi-agent architecture
- ICP-driven prospecting
- CRM automation
- Personalized outreach

## Business Impact

- Faster prospecting
- Automated CRM updates
- Personalized outreach at scale

## Key Skills Demonstrated

- Multi-Agent AI
- Prompt Engineering
- CRM Automation

---

# Workflow 3: AI Proposal Generator

## Objective

Generate proposals, email clients, create PandaDoc contracts, and send them for e-signature.

## Workflow


```text
Zapier Form
(Capture Client Inquiry)
        ↓
OpenAI
(Generate Proposal Content)
        ↓
Google Slides
(Create Proposal from Template)
        ↓
Gmail
(Email Proposal to Client)
        ↓
PandaDoc API
(Create Contract Draft)
        ↓
Delay
(Wait for Document Processing)
        ↓
PandaDoc API
(Check Document Status)
        ↓
PandaDoc API
(Send Contract for E-signature)
```

## Features

- AI proposal generation
- Google Slides automation
- PandaDoc integration
- Contract automation

## Business Impact

- Faster proposals
- Standardized documents
- Reduced administrative work

## Key Skills Demonstrated

- API Integration
- Document Automation
- Workflow Automation

---

# Technologies Used

- Claude API / Claude Code
- OpenAI
- n8n
- Zapier
- Airtable
- Pipedrive
- Google Workspace
- PandaDoc API
- REST APIs

---

# Skills Demonstrated

- AI Workflow Automation
- AI Agent Design
- Workflow Orchestration
- Airtable Application Design
- CRM Automation
- Business Process Automation
- Human-in-the-Loop Systems
- REST API Integration
- Sales Automation
- Claude API Integration & Structured Output
- Rate Limit / Retry / Error Handling
- Automated Testing (mocked external dependencies)

---

# Repository Structure

```text
.
├── workflow-1-ai-airtable-sales-automation-platform/
│   ├── assets/
│   ├── docs/
│   ├── workflows/
│   ├── architecture.md
│   └── README.md
│
├── workflow-2-ai-business-development/
│   ├── icp-examples/
│   ├── screenshots/
│   ├── workflow-json/
│   ├── architecture.md
│   └── README.md
│
├── workflow-3-ai-proposal-generator/
│   ├── assets/
│   ├── screenshots/
│   ├── architecture.md
│   ├── prompt.md
│   └── workflow.json
│
├── workflow-4-ai-support-ticket-triage/
│   ├── data/
│   ├── scripts/
│   ├── src/
│   │   ├── cli.py
│   │   ├── webhook_server.py
│   │   └── triage/
│   ├── tests/
│   ├── dashboard.html
│   ├── architecture.md
│   └── README.md
```

---

# Future Improvements

- Lead enrichment
- Email verification
- Reply detection
- AI lead scoring
- Slack notifications
- Analytics dashboards
- Calendar integration
- Push Workflow 4's human-review queue into Airtable

---

# About Me

**Jerome Isaac Katigbak**

AI Automation Engineer passionate about building AI agents, workflow automations, and business process solutions using n8n, Zapier, OpenAI, and modern APIs.





