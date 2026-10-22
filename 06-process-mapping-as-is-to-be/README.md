# 06 - Process mapping: AS-IS vs TO-BE for Procure-to-Pay and Invoice-to-Cash

Product managers for finance automation must map how work happens today (AS-IS), where it breaks, and what the agentic version (TO-BE) should do, including where humans stay in control. This project does that for two core finance flows, and ranks which steps to automate first.

Based on general finance-operations practice and public descriptions of AP/AR automation. Time and volume figures in `opportunity_scoring.py` are **assumptions** to show the method; real values come from customer discovery (see project 08).

## A. Procure-to-Pay (accounts payable)

### AS-IS (manual)
```mermaid
flowchart LR
  A[Purchase request] --> B[Create PO in ERP]
  B --> C[Goods received - GRN]
  C --> D[Invoice arrives by email/PDF]
  D --> E[Manual data entry into ERP]
  E --> F[Manual 3-way match: PO vs GRN vs invoice]
  F -->|mismatch| G[Email chain with vendor / buyer]
  F -->|match| H[Approval by email]
  G --> F
  H --> I[Payment run]
  I --> J[Manual bank reconciliation]
```
Pain points: re-keying invoice data (errors), chasing approvers by email, duplicates paid twice, no visibility of status for vendors ("where is my payment?"), month-end reconciliation crunch.

### TO-BE (agentic, human in the loop)
```mermaid
flowchart LR
  A[Invoice arrives: email / portal / WhatsApp] --> B[AI capture: extract fields + confidence]
  B --> C[Auto 3-way match + duplicate check]
  C -->|clean + high confidence| D[Auto-route for approval]
  C -->|exception| E[Exception inbox: reason + suggested fix]
  E --> F[Human resolves - label feeds quality metrics]
  F --> C
  D --> G[Approve in Slack / WhatsApp]
  G --> H[Scheduled payment]
  H --> I[Auto reconciliation + audit trail]
```
Human control points: low-confidence extraction, any exception, payments above a threshold, vendor bank-detail changes.

## B. Invoice-to-Cash (accounts receivable)

### AS-IS
```mermaid
flowchart LR
  A[Create invoice] --> B[Send by email]
  B --> C[Wait]
  C --> D[Clerk checks aging report]
  D --> E[Manual reminder / phone call]
  E --> F{Paid?}
  F -->|no| D
  F -->|yes| G[Manual cash application]
```
### TO-BE
```mermaid
flowchart LR
  A[Invoice issued + customer portal link] --> B[Automatic reminder sequence]
  B --> C{Customer replies / disputes?}
  C -->|dispute| D[Hand off to human + log reason]
  C -->|promise to pay| E[Track promised date + day-before reminder]
  C -->|no response| F[Voice agent call within policy]
  E --> G[Payment received]
  F --> G
  G --> H[Auto cash application + exceptions]
```
Guardrails (from project 02): correct amount and date, no threats, no invented discounts, always hand off disputes.

## C. Exception taxonomy (shared by both flows)
| Exception | Example | Who resolves | Automation idea |
|---|---|---|---|
| Price mismatch | Invoice price > PO price | Buyer | Suggest tolerance rule + request credit note |
| Quantity mismatch | Billed > received | Warehouse/buyer | Auto-request GRN update |
| Duplicate | Same invoice sent twice | AP clerk | Block + notify vendor |
| Missing PO | No PO reference | Procurement | Match by vendor + amount, ask requester |
| Vendor change | New bank details | Finance + security | Always human, call-back verification |
| Dispute | Customer says invoice is wrong | AR + account owner | Hand-off with full context |

## D. Which steps to automate first?
`opportunity_scoring.py` ranks steps by (monthly volume x minutes saved) divided by (build effort x risk), using **assumed** inputs, and writes `results/opportunities.md`. Change the inputs and re-run when real customer data exists.

Run: `python opportunity_scoring.py`
