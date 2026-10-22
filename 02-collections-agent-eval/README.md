# 02 - Evaluating an AI collections agent

**Product question:** before an agent contacts real customers about overdue invoices, how do we measure whether its messages are safe, and which checks need an LLM judge?

**Data (synthetic, seeded):** 800 overdue-invoice records, each with an agent message that has injected defects with known ground truth:
- Factual or structural: wrong amount, wrong due date, missing payment link, missed hand-off on a disputed invoice.
- Subjective: threatening tone, invented discount/offer. About 30% of these are paraphrased so keyword rules cannot see them.

**Method:** a deterministic checker (regex + keyword rules) is scored against ground truth with precision, recall and bootstrap 95% confidence intervals.

| Defect | Count | Checker precision | Checker recall | Recall 95% CI |
|---|---|---|---|---|
| Wrong amount | 58 | 1.00 | 1.00 | 1.00-1.00 |
| Wrong date | 38 | 1.00 | 1.00 | 1.00-1.00 |
| Missing link | 32 | 1.00 | 1.00 | 1.00-1.00 |
| Missed hand-off | 29 | 1.00 | 1.00 | 1.00-1.00 |
| Threatening tone | 51 | 1.00 | 0.61 | 0.49-0.75 |
| Invented offer | 32 | 1.00 | 0.63 | 0.47-0.78 |

**Headline findings**
- Trusting the checker alone reports a **77.4%** pass rate; the true rate is **74.4%**.
- It missed **24 of 184** messages that had a critical defect (13%).
- Rules are enough for factual checks. Tone and invented offers need a judge model, and the judge must be calibrated.

**Next step (code included, not run):** `llm_judge.py` has the rubric prompt, a JSON-parsing judge wrapper, and a calibration function (agreement, Cohen's kappa, recall, precision against human labels). Proposed release gate: zero critical factual defects in the last 500 messages and judge-human kappa >= 0.7, plus a weekly 50-message human audit.

Outputs: `results/metrics.json`, `results/messages_and_labels.csv`, `results/checker_vs_truth.png`.
