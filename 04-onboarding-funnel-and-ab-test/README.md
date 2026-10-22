# 04 - Onboarding funnel and A/B test (product analytics)

**Product question:** new finance teams sign up for a B2B SaaS product, but many never get value. Where do we lose them, and does a one-click ERP connection flow improve activation without hurting support load?

**Data:** 20,000 simulated signups (company size, acquisition channel) moving through: signed up -> connected ERP -> processed first invoice -> activated (3+ invoices in 7 days) -> still active in week 4. **Synthetic and seeded; the effect sizes are injected so the method can be checked.**

## 1. Funnel
| Stage | Users | % of signups | Step conversion |
|---|---|---|---|
| Signed up | 20,000 | 100% | - |
| Connected ERP | 9,385 | 46.9% | 46.9% |
| Processed first invoice | 7,388 | 36.9% | 78.7% |
| Activated | 4,368 | 21.8% | 59.1% |
| Active in week 4 | 3,118 | 15.6% | 71.4% |

**Biggest drop-off: connecting the ERP** (only 47% get past it). It is worst for **Enterprise (31%)** versus SMB (52%), and for **Paid** traffic (43%) versus Partner (53%).

## 2. Experiment design (before running it)
- Primary metric: ERP connection rate. Baseline 46.9%. Minimum detectable effect +2 percentage points, alpha 0.05, power 0.80 -> **9,794 users per arm**.
- Guardrail: support tickets per user. Check sample-ratio mismatch (should be 50/50).

## 3. Result
| | Control | Variant (one-click connect) |
|---|---|---|
| Users | 9,794 | 9,794 |
| ERP connection rate | 45.9% | 49.8% |
| Lift | | **+4.0 pp** (95% CI +2.6 to +5.4), p < 0.0001 |
| Support tickets per user | 0.304 | **0.330** (p = 0.0012) |
| Sample ratio check | p = 1.00 | (balanced) |

## 4. Decision (what a PM would write)
**Do not ship to everyone yet.** The primary metric improved clearly, but support tickets rose by about 8.6% and that increase is statistically significant. Next steps: (1) read the tickets to find which step confuses people, (2) fix it and re-test, or (3) release first to the segment that gains most (Enterprise) while monitoring tickets.

**What I would not conclude:** that the flow raises long-term retention. The test only measured connection and tickets; I would track activation and week-4 retention for the exposed cohort before claiming that.

Run: `python run_analysis.py`. Outputs in `results/` (`metrics.json`, `funnel_and_experiment.png`).
