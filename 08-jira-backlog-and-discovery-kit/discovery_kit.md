# Customer discovery kit (method and templates)

**No findings are included.** I have not interviewed anyone; this is the plan and templates I would use. Every hypothesis in this repo is to be tested with these before building.

## 1. Research goals
1. Understand how finance teams handle invoices and collections today (AS-IS) and where time is lost.
2. Find what they need to see before trusting an AI agent (quality, control, auditability).
3. Learn which ERPs and channels (email, WhatsApp, Slack) matter and what is customised.

## 2. Who to talk to (screener)
- Finance managers/controllers, AP/AR clerks, implementation or finance-ops leads at companies processing 300+ invoices per month.
- Mix of company sizes and at least 3 ERPs. Exclude people who have never handled invoices themselves.
- Target 8-10 interviews, 30-40 minutes each.

## 3. Interview guide
Warm-up: role, team size, tools. Then:
1. Walk me through the last invoice you processed, from arrival to payment. What happened at each step?
2. Where did it get stuck or need rework? How often does that happen? How long does a typical exception take?
3. Show me how you decide whether an invoice can be paid. What do you check?
4. How do approvals work today? Who do you chase and how?
5. How do you follow up on overdue invoices? What do you say? What goes wrong?
6. Tell me about a time an automated tool made a mistake. What happened next?
7. What would you need to see before letting software contact your customers on your behalf?
8. Which numbers do you report to your manager each month?
9. Which ERP/accounting tools do you use, and what is custom about your setup?
10. If you could change one thing about this process, what would it be?
Rules: ask about past behaviour, not opinions about my idea; never lead; ask "why" and "what happened next"; record exact words.

## 4. Quantify the pain (time and error log)
| Task | Items per week | Minutes per item | Error/rework rate | Who does it |
|---|---|---|---|---|
Ask each participant to estimate and, where possible, show a week of real data.

## 5. Hypotheses to test
| # | Hypothesis | Evidence that would support it | Evidence that would refute it |
|---|---|---|---|
| H1 | Finance managers will raise automation only with a visible quality score | Ask for metrics before enabling; mention audit worries | Say they trust the vendor without proof |
| H2 | Exceptions take most of the time, not clean invoices | Exceptions > 50% of handling time | Clean invoices dominate effort |
| H3 | WhatsApp/Slack approvals are preferred over email | Approvers already live in chat | Security/policy bans chat approvals |
| H4 | ERP integration is the main adoption blocker | Delays or failures cited | Rarely mentioned |

## 6. Synthesis template
| Participant | Role/company size | Key quotes | Pain points (ranked) | Workarounds | Tools/ERP | Hypotheses supported / refuted |
|---|---|---|---|---|---|---|
After all interviews: group quotes into themes, count how many participants mention each, rank by frequency x severity, and write 3 insights as "People struggle to ___ because ___, so they ___."

## 7. From insights to backlog
Each insight becomes an epic or story in `jira_backlog.csv`, with a metric and a way to measure success. Re-prioritise with RICE after the interviews replace my assumed numbers.
