# 05 - Agent Quality Scorecard: wireframe

A one-screen design for the product bet in `03-product-case`: show finance managers how safe and accurate an AI collections agent is, let them choose an automation-vs-risk level, and lock go-live behind objective checks.

Files: `scorecard.html` (open in a browser) and `scorecard.png` (screenshot).

**Design decisions**
- Lead with three numbers a finance manager understands: pass rate, critical defects, judge-vs-human agreement.
- Split defects by whether rules can catch them ("needs judge" column), so reviewers spend time where rules fail (project 02).
- Make the automation-vs-risk dial explicit (project 01): conservative 59% STP / 0% risk, balanced 75% STP / ~1.3% risk.
- Review queue turns every reviewer decision into a human label that recalibrates the judge.
- Go-live is locked until: zero critical factual defects in the last 500 messages, judge kappa >= 0.70, weekly human audit done.

**Honesty note:** the pass rate, defect counts and the conservative/balanced figures come from the synthetic experiments in this repo. Anything marked "not yet measured" would need real pilot data.
