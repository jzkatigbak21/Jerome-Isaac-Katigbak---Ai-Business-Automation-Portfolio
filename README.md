<img width="1693" height="929" alt="repository banner-1" src="https://github.com/user-attachments/assets/763a3998-2480-4ded-99b9-9b1a3fbe5305" />

# AI Business Automation Portfolio

## Overview

This repository showcases three production-style AI automation projects built to streamline business development, outbound sales, and proposal generation. Each project demonstrates how AI, workflow automation, APIs, and business applications can be combined to solve real operational problems.

The portfolio focuses on practical implementations using **n8n**, **Airtable**, **OpenAI**, **Zapier**, and modern APIs with an emphasis on modular workflow design and human-in-the-loop automation.

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

# Technologies Used

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

---

# About Me

**Jerome Isaac Katigbak**

AI Automation Engineer passionate about building AI agents, workflow automations, and business process solutions using n8n, Zapier, OpenAI, and modern APIs.





