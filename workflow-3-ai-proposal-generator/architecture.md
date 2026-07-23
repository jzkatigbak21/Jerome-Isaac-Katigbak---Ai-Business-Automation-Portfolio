# Workflow Architecture

## Overview

This workflow automates the proposal generation and contract preparation process for new client inquiries using AI, Google Workspace, Gmail, and PandaDoc.

The workflow begins when a new client submits a request through Zapier Forms. An AI model generates a customized business proposal based on the submitted requirements. The proposal is automatically inserted into a Google Slides presentation, converted into a shareable presentation, and emailed to the client.

After the proposal is delivered, the workflow creates a PandaDoc contract from a predefined template. Once the document is ready, the workflow waits briefly for PandaDoc to finish processing before automatically sending the contract for electronic signature.

This workflow eliminates manual proposal preparation while reducing turnaround time from lead submission to contract delivery.

---

## Zapier Diagram

<img width="561" height="840" alt="1  workflow-overview" src="https://github.com/user-attachments/assets/934d27d3-4eda-49ca-b753-4998c7fa073a" />


---

## System Architecture

```text
                Zapier Form Submission
                         │
                         ▼
                 OpenAI (GPT-5.5)
          Generate Proposal Content
                         │
                         ▼
        Google Slides Template Engine
        Create Presentation from Template
                         │
                         ▼
                Gmail Integration
             Send Proposal Email
                         │
                         ▼
              PandaDoc API (Create Draft)
                         │
                         ▼
                  Delay (10 Seconds)
                         │
                         ▼
         PandaDoc API (Check Document Status)
                         │
                         ▼
                 Document Ready?
                  │            │
                No             Yes
                │               │
                ▼               ▼
          Stop Workflow   PandaDoc API
                           Send Contract
```

---

## Design Philosophy

This workflow follows an event-driven automation architecture.

Rather than requiring manual proposal writing and contract preparation, every stage of the client onboarding process is orchestrated automatically after a form submission.

Each service is responsible for one clearly defined business function:

- AI generates proposal content
- Google Slides creates the presentation
- Gmail delivers the proposal
- PandaDoc prepares the contract
- PandaDoc manages electronic signatures

This modular design allows individual components to be replaced or extended without redesigning the entire workflow.

---

## Workflow Responsibilities

### Zapier Forms

#### Purpose

Captures client information that initiates the workflow.

#### Responsibilities

- Receive client details
- Capture project requirements
- Trigger the automation

---

### OpenAI

#### Purpose

Generate a customized business proposal using the submitted project information.

#### Responsibilities

- Analyze the client request
- Produce structured proposal content
- Personalize recommendations
- Generate professional business copy

---

### Google Slides

#### Purpose

Create a presentation from a predefined proposal template.

#### Responsibilities

- Populate placeholders
- Preserve branding
- Generate a presentation automatically
- Produce a client-ready proposal

---

### Gmail

#### Purpose

Deliver the proposal to the client.

#### Responsibilities

- Compose the email
- Attach or link the proposal
- Send the proposal automatically

---

### PandaDoc

#### Purpose

Generate and send a legally binding electronic contract.

#### Responsibilities

- Create a contract draft
- Populate recipient information
- Monitor document readiness
- Send the contract for electronic signature

---

## Integration Flow

| Step | Service | Purpose |
|------|---------|---------|
| 1 | Zapier Forms | Receive new client inquiry |
| 2 | OpenAI | Generate proposal content |
| 3 | Google Slides | Build proposal presentation |
| 4 | Gmail | Email proposal to client |
| 5 | PandaDoc | Create contract draft |
| 6 | Delay | Allow PandaDoc processing |
| 7 | PandaDoc | Check document status |
| 8 | PandaDoc | Send contract for e-signature |

---

## Design Decisions

### Why Google Slides?

Using a presentation template ensures every proposal maintains consistent branding while allowing AI-generated content to be inserted dynamically.

### Why PandaDoc?

PandaDoc provides document generation, recipient management, status tracking, and legally compliant electronic signatures through a single API.

### Why Wait Before Sending?

After a draft is created, PandaDoc requires time to finish generating the document.

Instead of attempting to send the contract immediately, the workflow introduces a short delay before checking the document status. This ensures the document reaches the `document.draft` state before calling the Send Contract endpoint.

---

## Future Improvements

Potential enhancements include:

- Dynamic pricing calculations
- Multiple proposal templates by industry
- CRM integration (HubSpot or Pipedrive)
- Automated follow-up reminders
- Payment link generation
- Approval workflow before proposal delivery
- PDF generation and cloud storage
- Slack or Microsoft Teams notifications
- Client portal integration
- Proposal analytics and tracking
