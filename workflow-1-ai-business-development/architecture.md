# Workflow Architecture

## Overview

This workflow automates outbound lead generation for an AI automation agency using a multi-agent architecture built in n8n.

The workflow is triggered whenever an Ideal Customer Profile (ICP) document stored in Google Drive is updated. The ICP is retrieved from Google Docs and passed to a Business Development Manager AI Agent, which orchestrates three specialized sub-agents responsible for prospect discovery, CRM management, and personalized outreach.

Instead of relying on a single AI agent to complete every task, the workflow follows a **manager-worker architecture**, where each agent has a clearly defined responsibility. This modular approach improves maintainability, scalability, and prompt specialization.

---
## n8n Workflow
<img width="1081" height="563" alt="workflow-overview png" src="https://github.com/user-attachments/assets/9f3c0fc5-dd07-4c11-813b-34e2b04d7678" />


# System Architecture

```text
                    Google Drive Trigger
                   (ICP Document Updated)
                             │
                             ▼
                    Google Docs Node
                   (Retrieve ICP Content)
                             │
                             ▼
        ┌────────────────────────────────────┐
        │ Business Development Manager Agent │
        │         (Orchestrator)             │
        └────────────────────────────────────┘
                   │          │
                   │          │
                   ▼          ▼
        ┌────────────────┐
        │ Prospecting    │
        │ Sub-agent      │──────────────┐
        └────────────────┘              │
                   │                    │
                   ▼                    │
      Internet Search + Hunter.io       │
                                        │
                                        ▼
                          ┌────────────────────┐
                          │ RevOps Sub-agent   │
                          └────────────────────┘
                                     │
                                     ▼
                             Pipedrive CRM
                                     │
                                     ▼
                          ┌────────────────────┐
                          │ SDR Sub-agent      │
                          └────────────────────┘
                                     │
                                     ▼
                           Gmail Draft Creation
                                     │
                                     ▼
                          Success / Failure
                           Notification
```

---

# Design Philosophy

This workflow follows a **manager-worker multi-agent architecture**.

The Business Development Manager Agent is responsible for orchestration only. Rather than performing every task itself, it delegates specialized responsibilities to dedicated sub-agents.

This approach provides several advantages:

- Separation of responsibilities
- Easier prompt maintenance
- Better scalability
- More reusable AI agents
- Improved debugging and testing
- Easier replacement of individual components without affecting the entire workflow

---

# AI Agent Responsibilities

## Business Development Manager

### Purpose

Acts as the workflow orchestrator.

This agent never performs prospecting or CRM operations directly. Instead, it coordinates the specialized sub-agents and ensures they execute in the correct sequence.

### Responsibilities

- Analyze the Ideal Customer Profile (ICP)
- Generate an appropriate prospecting query
- Call the Prospecting Sub-agent
- Call the RevOps Sub-agent for each prospect
- Call the SDR Sub-agent once all prospects are stored
- Return a workflow execution summary

### System Prompt

```text
You are the Business Development Manager Agent for AutomateAI, an AI automation agency.

You are provided with the Ideal Customer Profile (ICP).

Your objective is to identify qualified prospects that match the ICP and prepare them for personalized outreach.

Follow these steps exactly:

1. Analyze the ICP to identify the target industry, ideal job titles, company size, location, and business challenges.

2. Use your Prospecting Sub-agent tool ONCE to search online for qualified prospects, providing a search query based on the ICP.

Requirements:
- Find up to 4 high-quality prospects whenever possible.
- Prioritize decision-makers with influence over automation, operations, digital transformation, technology, or executive leadership, depending on the ICP.
- Avoid duplicate companies and duplicate contacts.
- If fewer than 4 qualified prospects can be found, return the best available matches.

3. For each prospect identified, use your RevOps Sub-agent tool to create a Person record in the Pipedrive CRM database. Use the tool repeatedly, once for each prospect.

4. After all prospects have been added to Pipedrive, use your SDR Sub-agent tool ONCE. This tool will retrieve all newly created prospects from Pipedrive and generate personalized outbound sales email drafts.

5. Reply with a concise summary that includes:
- Number of prospects found
- Number of prospects added to Pipedrive
- Number of email drafts created
- Any issues encountered during execution.


```

---

## Prospecting Sub-agent

### Purpose

Identifies qualified companies and decision-makers that match the supplied ICP.

### Responsibilities

- Search the web for qualified prospects
- Verify company relevance
- Identify decision-makers
- Find business email addresses
- Return up to three qualified prospects
- Avoid duplicate companies and contacts

### System Prompt

```text
You are a Prospecting Agent for AutomateAI, an AI automation agency.

Your job is to identify qualified sales prospects based on the user's search query.

Use your available tools to:
- Search the internet for companies that match the requested Ideal Customer Profile (ICP).
- Visit company websites when necessary to verify that they fit the ICP.
- Identify the most relevant decision-maker for each company.
- Find the most likely business email address for that decision-maker using your available tools.

Requirements:
- Return 4 high-quality prospects.
- Prioritize decision-makers involved in technology, operations, digital transformation, automation, or executive leadership, depending on the ICP.
- Avoid duplicate companies and duplicate contacts.
- Only include prospects that closely match the ICP.

```

---

## RevOps Sub-agent

### Purpose

Maintains CRM data integrity by creating structured prospect records inside Pipedrive.

### Responsibilities

- Receive prospect information
- Create Person records
- Preserve data accuracy
- Return confirmation after successful creation

### System Prompt

```text
Based on the input of the user, you should reply with a structured version of the lead. Your reply will be sent to Pipedrive to create a lead record.
```

---

## SDR Sub-agent

### Purpose

Generates personalized HTML email drafts for every qualified prospect stored in Pipedrive.

Emails are saved as Gmail drafts for human review before sending.

### Responsibilities

- Retrieve newly created CRM contacts
- Generate personalized outreach emails
- Create Gmail drafts
- Focus messaging on AI automation services
- Encourage prospects to schedule a discovery call

### System Prompt

```text
You are an SDR for AutomateAI, an AI automation agency.

Use your tool to retrieve all Person records from Pipedrive.

For each person, create a personalized outbound sales email from Thea Mejos, Business Development Director at AutomateAI.

The email should:
- Be professionally formatted in HTML.
- Be personalized to the prospect's role, company, and industry.
- Explain how AI automation can eliminate repetitive work, streamline business processes, and improve operational efficiency.
- Avoid making claims that are not supported by the available prospect information.
- End with a clear call to action inviting the prospect to schedule a discovery call or reply to the email to learn more.

Do not invent company details, client results, or services beyond AI automation and workflow optimization.

```

---

# Design Decisions

### Why a Multi-Agent Architecture?

A single AI agent could technically perform every task in this workflow, but dividing responsibilities among specialized agents provides several benefits.

| Decision | Benefit |
|----------|---------|
| Separate Prospecting Agent | Easier to improve search quality independently |
| Separate RevOps Agent | Keeps CRM operations isolated and reusable |
| Separate SDR Agent | Allows independent optimization of outreach emails |
| Business Development Manager | Centralized orchestration and easier workflow expansion |

This modular architecture also makes it straightforward to add new capabilities, such as Lead Scoring, Company Research, or Calendar Scheduling, without modifying the existing agents.

---

# Future Improvements

Potential enhancements include:

- AI-powered lead scoring before CRM insertion
- Duplicate detection in Pipedrive
- Retrieval-Augmented Generation (RAG) for company research
- Automatic follow-up email sequences
- Calendar booking integration
- Slack or Microsoft Teams notifications
- Company enrichment using additional data providers
- Human approval step before CRM insertion
- Human approval step before Gmail draft creation
