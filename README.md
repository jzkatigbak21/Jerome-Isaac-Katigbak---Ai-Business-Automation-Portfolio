<img width="1693" height="929" alt="repository banner-1" src="https://github.com/user-attachments/assets/763a3998-2480-4ded-99b9-9b1a3fbe5305" />

# AI Business Automation Portfolio

## Overview

This repository showcases four production-style AI automation projects covering business development, outbound sales, proposal generation, and support ticket triage. Each project demonstrates how AI, workflow automation, APIs, and business applications can be combined to solve real operational problems.

The portfolio focuses on practical implementations using **n8n**, **Airtable**, **OpenAI**, **Zapier**, and modern APIs with an emphasis on modular workflow design and human-in-the-loop automation. Workflow 4 is built differently on purpose: no low-code platform in the pipeline, just Python and the **Claude API** directly, with its own retry/concurrency handling and test suite -- built end-to-end with **Claude Code**.

---

## 🎥 Portfolio Walkthrough

https://drive.google.com/file/d/1fF5a4NLAII7zrC4AENpJL3Msu7EMgk1A/view?usp=drive_link
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

# Workflow 4: AI Support Ticket Triage

## Objective

Batch-classify support tickets/reviews (sentiment, urgency, category,
entities), draft ready-to-send replies for straightforward cases, and
flag sensitive tickets for human review -- built directly against the
Claude API with Claude Code, not orchestrated through a low-code
platform.

## Workflow

```text
CSV of Tickets
(Shopify/Gorgias export or synthetic dataset)
        ↓
Bounded-Concurrency Batch Dispatch
(ThreadPoolExecutor, rate-limit aware)
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
CSV Output
(results.csv / human_review_queue.csv / failures.csv)
```

## Features

- Structured output via forced Claude tool-use (no brittle JSON parsing)
- Exponential backoff + jitter retries on rate limits, timeouts, 5xx errors
- Bounded concurrency batch processing, tested at 300-ticket volume
- Keyword + confidence-floor safety net independent of the model's own judgment
- Per-ticket failure isolation
- Offline unit test suite covering retry logic, safety-net logic, and batch failure isolation

## Business Impact

- Cuts manual triage time on repetitive tickets
- Keeps sensitive/risky tickets in front of a human before anything is sent
- Batch-processes at volume instead of one ticket at a time

## Key Skills Demonstrated

- Claude API Integration (structured output, tool use)
- Rate Limit / Retry / Error Handling
- Concurrent Batch Processing
- Prompt Design
- Defensive Engineering
- Automated Testing
- Built with Claude Code

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
│   │   └── triage/
│   ├── tests/
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
- Live Gorgias/Shopify ticket ingestion for Workflow 4
- Push Workflow 4's human-review queue into Airtable

---

# About Me

**Jerome Isaac Katigbak**

AI Automation Engineer passionate about building AI agents, workflow automations, and business process solutions using n8n, Zapier, OpenAI, and modern APIs.





