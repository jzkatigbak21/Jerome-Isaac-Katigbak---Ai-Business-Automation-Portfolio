<img width="1823" height="863" alt="repository banner" src="https://github.com/user-attachments/assets/17a5f66c-b4f0-4e87-884d-dccccfb5445e" />

# AI Business Automation Portfolio

## Overview

This repository showcases two AI-powered business automation workflows that streamline the sales process from lead generation to proposal creation and contract delivery.

These projects demonstrate practical applications of AI agents, workflow automation, CRM integration, document generation, and API orchestration using modern no-code/low-code tools.

---

# Workflow 1: AI Business Development Manager

## Objective

Automatically identify qualified prospects from an Ideal Customer Profile (ICP), store them in a CRM, generate personalized outreach emails, and create Gmail drafts for review before sending.

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

- Reads an Ideal Customer Profile (ICP) from Google Docs
- Uses a multi-agent architecture
- Searches online for qualified prospects
- Finds business contact information
- Stores prospects in Pipedrive CRM
- Generates personalized outbound HTML email drafts
- Creates Gmail draft emails for review
- Supports multiple industries by simply changing the ICP

## Business Impact

- Automates lead generation based on a customizable Ideal Customer Profile (ICP).
- Reduces manual prospect research by identifying and qualifying prospects with AI.
- Eliminates repetitive CRM data entry through automated Pipedrive integration.
- Produces personalized outreach emails at scale while maintaining human review through Gmail drafts.
- Enables sales teams to launch targeted outbound campaigns faster and with greater consistency.
  
## Key Skills Demonstrated

- Multi-Agent AI Systems
- Prompt Engineering
- Lead Generation Automation
- CRM Integration (Pipedrive)
- AI-Assisted Sales Development
- Google Workspace Automation
- Workflow Orchestration with n8n

## AI Agents

### Business Development Manager

Coordinates the entire workflow by analyzing the ICP and delegating tasks to specialized AI agents.

### Prospecting Agent

- Searches the web for qualified prospects
- Identifies relevant decision-makers
- Finds business email addresses
- Returns up to three qualified leads

### RevOps Agent

Creates Person records inside Pipedrive CRM for each qualified prospect.

### SDR Agent

Generates personalized HTML email drafts for every prospect stored in the CRM.

---

# Workflow 2: AI Proposal Generator & Contract Automation

## Objective

Automatically generate a proposal, email it to the client, create a PandaDoc contract, and send it for electronic signature.

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

- Captures client information using Zapier Forms
- Generates customized proposal content with OpenAI
- Creates branded Google Slides proposals from a template
- Sends proposals automatically via Gmail
- Creates PandaDoc contracts through the REST API
- Waits for PandaDoc document processing
- Automatically sends contracts for electronic signature

---
## Business Impact

- Reduces proposal creation time by automatically generating customized client proposals.
- Standardizes proposal quality using reusable Google Slides templates.
- Accelerates the sales cycle by automatically creating and sending contracts for e-signature.
- Eliminates manual document creation and repetitive administrative tasks.
- Improves the client onboarding experience through a seamless proposal-to-contract workflow.


# Technologies Used

## AI

- OpenAI GPT

## Automation

- n8n
- Zapier

## Google Workspace

- Google Drive
- Google Docs
- Google Slides
- Gmail

## CRM

- Pipedrive

## Document Automation

- PandaDoc REST API

---

# Skills Demonstrated

- AI Agent Design
- Multi-Agent Orchestration
- Prompt Engineering
- Workflow Automation
- REST API Integration
- CRM Automation
- Business Process Automation
- Sales Automation
- Lead Generation
- Google Workspace Automation
- Document Generation
- API Authentication
- AI-Powered Personalization

---

# Future Improvements

- AI-powered lead scoring
- CRM duplicate detection
- Automated follow-up email sequences
- Proposal version management
- Calendar scheduling integration
- Slack or Microsoft Teams notifications
- Analytics dashboard
- Retrieval-Augmented Generation (RAG) for company research

---

# Author

**Jerome Isaac Katigbak**

Aspiring AI Automation Engineer passionate about building AI agents, workflow automations, and business process solutions using n8n, Zapier, OpenAI, and modern APIs.

---

## Repository Structure

```text
.
├── Workflow 1 - AI Business Development Manager
│   ├── README.md
│   ├── workflow.json
│   ├── screenshots/
│   └── prompts/
│
├── Workflow 2 - AI Proposal Generator & Contract Automation
│   ├── README.md
│   ├── workflow.json
│   ├── screenshots/
│   └── templates/
│
└── assets/
    ├── architecture-diagrams
    └── demo-images
```
