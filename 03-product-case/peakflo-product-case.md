# Product case: making AI collections agents measurable and trustworthy

Based only on public information about Peakflo (peakflo.co) plus my own experiments in this repo.
Everything marked **[Hypothesis]** is my idea to test, not a fact about the company. Numbers marked **[Assumption]** are placeholders to be replaced with real data.

---

## 1. Context (what I understand)

Peakflo automates finance operations for businesses: accounts payable (invoice capture, 2/3-way matching, approvals, payments, vendor portal) and accounts receivable (invoicing, reminders, customer portal, cash application, collections). Its newer layer is agentic: AI voice agents for collections, browser agents that operate web systems, WhatsApp agents, and workflows that evaluate themselves with LLM-as-a-judge.

**Core tension for any finance AI product:** automation creates value only if customers trust it enough to switch it on, and trust depends on measurable quality. One wrong amount in a collections call damages a customer relationship, so quality has to be provable, not asserted.

## 2. Users and jobs to be done

| User | Job | Pain today |
|---|---|---|
| AR clerk / collections owner | Get overdue invoices paid without damaging relationships | Chasing by hand, no view of which promises were kept |
| Finance manager / controller | Know cash will arrive and that the agent is safe | Cannot audit what the agent said or why |
| Customer being contacted | Resolve the invoice quickly, fairly | Repeated, tone-deaf or wrong reminders |
| Peakflo implementation/support | Roll out agents to new customers fast | Hard to prove quality before go-live |

## 3. Problems I would prioritise (evidence from my experiments)

1. **Rules catch factual mistakes but miss subjective ones.** In my synthetic evaluation (`02-collections-agent-eval`), a rules-only checker caught 100% of wrong amounts, wrong dates, missing payment links and missed hand-offs, but only **61% of threatening tone** and **63% of invented offers**. Trusting it alone would report a 77% pass rate when the true rate was 74%, and it missed **24 of 184** messages with a critical defect.
2. **Automation vs risk is a dial, not a switch.** In `01-invoice-matching-exceptions`, relaxing a strict 1% price tolerance to 3% lifted straight-through processing (STP) from **59% to 75%** while the false-approve rate stayed around **1.3%**. The product decision is which risk level each customer accepts, and customers should see and control it.
3. **Exceptions are where trust is won or lost.** Every invoice the system cannot finish needs a clear reason and a one-click fix.

## 4. Product bets (3) and prioritisation

| Bet | What | Metric | Reach | Impact | Confidence | Effort | RICE score* |
|---|---|---|---|---|---|---|---|
| A. Agent quality scorecard | Per-customer dashboard: match rate, STP rate, escalations, defects found by checks and by LLM judge | % of customers who raise automation level within 30 days | 8 | 3 | 0.7 | 4 | 4.2 |
| B. Promise-to-pay tracker | After each collections call/message, log the promised date and send a reminder the day before | Promise-kept rate; DSO | 7 | 2 | 0.6 | 3 | 2.8 |
| C. Exception inbox | One queue of everything the agent could not finish, with reason + one-click fix feeding the eval set | Median time to clear an exception | 9 | 2 | 0.7 | 5 | 2.5 |

*Reach (1-10), Impact (1-3), Confidence (0-1), Effort (person-weeks) are **[Assumption]** values to show the method; real values need customer data.
RICE = Reach x Impact x Confidence / Effort.

**Recommendation:** start with Bet A. It builds on a gap I measured, it creates trust, and it produces the labelled data that makes Bets B and C smarter.

## 5. Mini-PRD: Agent quality scorecard

**Problem.** Customers cannot see how safe or accurate the agent is, so they keep automation low.

**Goals.** (1) Show quality in plain numbers. (2) Let finance managers set the automation vs risk level. (3) Catch subjective defects (tone, invented offers) that rules cannot.

**Non-goals.** Replacing human review entirely; building a general analytics tool.

**User stories (with acceptance criteria)**
1. As a finance manager, I want a weekly quality score for the collections agent so that I can decide whether to expand it.
   - Given 50+ messages sent, when I open the scorecard, then I see pass rate, critical-defect count and a sample of failed messages.
2. As a finance manager, I want to choose a risk level (conservative / balanced / aggressive) so that the agent auto-approves only what I am comfortable with.
   - Given a chosen level, when invoices are processed, then STP rate and false-approve rate for that level are shown with a clear explanation.
3. As a collections owner, I want every message the agent flags for tone or invented offers to appear in a review queue so that I can correct it.
   - Given a flagged message, when I mark it correct/incorrect, then the label is stored for judge calibration.
4. As an implementation lead, I want a go-live gate so that a customer cannot enable calling until the quality threshold is met.
   - Given the last 500 messages, when critical factual defects > 0 or judge-human kappa < 0.7, then calling stays disabled and the reason is shown.
5. As a customer being contacted, I want to be handed to a person when I dispute an invoice so that I am not pushed to pay.
   - Given a dispute phrase, when the agent replies, then it hands off and logs the event.

**Success metrics**
- Primary: % of customers who increase automation level within 30 days of seeing the scorecard.
- Guardrails: critical-defect rate (target 0 factual), customer complaint rate, hand-off miss rate.
- Quality of the evaluator itself: judge-human agreement (Cohen's kappa >= 0.7) and weekly 50-message human audit.

**Risks and mitigations**
- Judge model bias or drift -> calibrate against humans and re-check weekly.
- Over-flagging annoys reviewers -> track precision and tune thresholds.
- Customers game the scorecard -> report raw counts alongside the score.

**Rollout.** Pilot with 5 customers who already use collections; compare automation-level changes against 5 who do not see the scorecard; decide after 4 weeks.

## 6. Metrics tree

North star: **cash collected on time** (lower DSO) at an acceptable complaint rate.
- Coverage: % of overdue invoices contacted -> connect rate -> promise-to-pay rate -> promise-kept rate.
- Quality: factual-defect rate, tone-defect rate, hand-off correctness.
- Trust: automation level chosen, scorecard views, review-queue completion.

## 7. First 30-60-90 days as an intern

- **30:** learn the AP/AR flows and the customer base; shadow customer calls; write the exception taxonomy; label 100 agent messages to start a calibration set.
- **60:** prototype the scorecard with real (anonymised) data; run the judge calibration; draft the PRD and review with engineering.
- **90:** ship an internal pilot to 3-5 customers; report impact and the next three bets.

## 8. What I would do differently with real data
Replace synthetic data and assumed RICE inputs with real customer segments, error logs and call recordings; and validate every hypothesis with 5-10 customer interviews before building.
