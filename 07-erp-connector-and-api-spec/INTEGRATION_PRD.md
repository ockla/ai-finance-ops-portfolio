# PRD: ERP integration for invoice posting

**Problem.** Finance teams will not switch on automation unless approved invoices post to their ERP accurately, exactly once, and visibly. Today integrations are slow to build and fail silently.

**Users.** Finance manager (needs trust and an audit trail), AP clerk (needs to see and fix failures), implementation engineer (needs fast onboarding of a new ERP).

## Goals
1. Post an approved invoice to the customer's ERP with no duplicates and no silent failures.
2. Make adding a new ERP a one-mapper task.
3. Give finance teams clear visibility of every sync, success or failure.

## Non-goals (v1)
Two-way sync of vendor master data; payments initiation; custom per-customer field logic beyond mapping.

## Requirements
| # | Requirement | Acceptance criteria |
|---|---|---|
| R1 | Canonical invoice model | Given invoices from email, portal or CSV, when processed, then all become one internal model before mapping |
| R2 | Validation before posting | Given an invoice whose lines do not add to the total, when submitted, then it is rejected with a reason and no ERP call is made |
| R3 | Idempotent posting | Given the same invoice submitted twice or retried, when posted, then exactly one ERP document exists |
| R4 | Retry on transient errors | Given a timeout/429/5xx, when posting, then retry up to 4 times with exponential backoff, then route to the exception inbox |
| R5 | Field mapping per ERP | Given ERP A/B/C, when posting, then number, vendor, date, currency, lines and total map correctly |
| R6 | Sync status visible | Given any invoice, when opened, then status (posted / duplicate / rejected / failed), ERP document id and attempts are shown |
| R7 | Alerting | Given failure rate > 2% over 1 hour, then notify the integration owner |

## Success metrics
- Sync success rate (first attempt) and eventual success rate (target >= 99%).
- Duplicate postings (target 0).
- Median time to onboard a new ERP (target: days, not weeks).
- Median time to resolve a failed sync.
- Guardrail: finance-team complaints about missing or wrong ERP entries.

## Risks and mitigations
| Risk | Mitigation |
|---|---|
| ERP API changes break mapping | Contract tests per ERP, versioned mappers, monitor error spikes |
| Rate limits | Backoff + queueing, respect Retry-After |
| Wrong data posted | Validation, dry-run mode for new customers, human approval step |
| Customers' custom fields | Phase 2: configurable mapping rules |

## Rollout
Pilot with 3 customers per ERP in dry-run mode (compare what we would post with what they post by hand) for 2 weeks, then live posting with alerts, then general availability.

## Open questions
Which ERPs do target customers use most? Which fields are custom? Do customers prefer API push or scheduled SFTP drop? (Answer through discovery interviews; see project 08.)
