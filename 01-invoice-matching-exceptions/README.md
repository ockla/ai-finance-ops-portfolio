# 01 - Invoice 3-way matching: rules vs ML

**Product question:** if we auto-approve invoices that look fine, how many can we straight-through-process (STP) without letting bad ones slip through?

**Data (synthetic, seeded):** 4,033 invoices tied to purchase orders and goods receipts, with labelled problems: price mismatch, over-billed quantity, duplicate, missing PO, wrong vendor. Harmless noise is included (rounding, vendor-name formatting) so a perfect rule is not trivial.

**Features:** price and quantity differences vs PO and goods receipt, fuzzy vendor-name similarity, duplicate flag, total difference.

**Compared on a held-out 30% test set**

| Approach | STP rate | False-approve rate* | Exception precision** | Macro F1 |
|---|---|---|---|---|
| Strict rules (1% tolerance) | 59.0% | 0.0% | 61.1% | 0.884 |
| Tuned rules (3% tolerance) | 75.3% | 1.3% | 100% | 0.995 |
| Random Forest | 74.2% | 1.0% | 96.2% | 0.983 |

*Share of truly bad invoices that were auto-approved (the costly mistake).  **Share of flagged invoices that were truly bad.

**What I learned (and what a PM would decide)**
- The strict rule is safe but sends 40% of invoices to humans, mostly false alarms (61% precision). Relaxing the tolerance gave +16 points of STP for ~1.3% risk. That is a **customer-facing dial**, not an engineering detail.
- At the default operating point the Random Forest only matched the tuned rules, because the injected errors follow simple rules. Its advantage shows when risk must be **zero**: sweeping the approval threshold, it reaches **68.4% STP at 0% false-approves** (exception precision 79%), versus **59.0%** for the strict rule at the same zero risk (+9 points), and 71.5% STP at 0.66% false-approves. I would confirm this on real exception data before claiming it.
- Most important features: duplicate flag, vendor similarity, PO found.

Outputs: `results/metrics.json`, `results/synthetic_invoices.csv`, `results/tradeoff_and_confusion.png`.
