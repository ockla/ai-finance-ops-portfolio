# AI Finance Ops: product + ML portfolio

Eight small, reproducible projects about one question: **how do you make AI automation in finance operations measurable, safe and worth switching on?**

All data is **synthetic** and seeded, so results are reproducible. This is a methodology portfolio, not a claim about any company's real data.

| Project | What it shows | Headline result |
|---|---|---|
| [01-invoice-matching-exceptions](01-invoice-matching-exceptions) | Accounts-payable 3-way matching: rules vs ML, STP rate vs risk | Tuning a price tolerance from 1% to 3% raised straight-through processing from **59% to 75%** at ~1.3% false-approves; at zero risk a Random Forest reached **68% STP vs 59%** for strict rules |
| [02-collections-agent-eval](02-collections-agent-eval) | Evaluating an AI collections agent; where rules end and an LLM judge is needed | A rules-only checker caught **100%** of factual defects but only **~61%** of tone and **~63%** of invented-offer defects; it missed **24 of 184** critical-defect messages |
| [03-product-case](03-product-case) | Product thinking: problems, RICE prioritisation, mini-PRD, metrics tree, 30-60-90 | Recommends an **agent quality scorecard** with a go-live gate |
| [04-onboarding-funnel-and-ab-test](04-onboarding-funnel-and-ab-test) | Product analytics: funnel, experiment design, A/B test with a guardrail | New flow lifted ERP connection **+4.0 pp** but raised support tickets **+8.6%** (both significant), so the call is: don't ship yet |
| [05-scorecard-wireframes](05-scorecard-wireframes) | UX/design: one-screen scorecard wireframe | Shows defects, the automation-vs-risk dial and a locked go-live gate |
| [06-process-mapping-as-is-to-be](06-process-mapping-as-is-to-be) | Process mapping for Procure-to-Pay and Invoice-to-Cash, exception taxonomy, automation scoring | AS-IS vs agentic TO-BE flows with human control points; 10 steps ranked by value, effort and risk |
| [07-erp-connector-and-api-spec](07-erp-connector-and-api-spec) | Integration design: canonical model, ERP mappers, idempotency, retries, OpenAPI, integration PRD | 15 unit tests pass; spec covers validation, duplicates, rate limits and ERP outages |
| [08-jira-backlog-and-discovery-kit](08-jira-backlog-and-discovery-kit) | Jira-ready backlog and customer-discovery plan | 3 epics, 13 stories, 61 points, validated CSV; discovery kit with no invented findings |

## Run it
```
pip install -r requirements.txt
python 01-invoice-matching-exceptions/run_experiment.py
python 02-collections-agent-eval/run_eval.py
python 04-onboarding-funnel-and-ab-test/run_analysis.py
python 06-process-mapping-as-is-to-be/opportunity_scoring.py
(cd 07-erp-connector-and-api-spec && python -m unittest -v)
python 08-jira-backlog-and-discovery-kit/make_backlog.py
```
Results (JSON, CSV, charts) are written to each project's `results/` folder.

## Honest limitations
- Data is synthetic: the injected errors are easier to separate than real-world ones.
- Project 2's LLM-judge code (`llm_judge.py`) is provided but not run, because it needs an API key.
- RICE inputs in project 3 and the volumes in project 6 are assumptions, shown to demonstrate the method.
- The ERP formats in project 7 are simplified, illustrative schemas, not any vendor's official ones.
- Project 8 is a method and templates; no customer interviews have been done.
