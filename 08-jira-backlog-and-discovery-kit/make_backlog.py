"""
Generates a Jira-importable backlog (CSV) for the product bets in this repo and validates it.
Import in Jira: Projects > Import issues from CSV; map Summary, Description, Priority, Labels,
Story Points, Epic Name (epics) and Epic Link (stories).
"""
import csv
from pathlib import Path

FIB = {1, 2, 3, 5, 8, 13}
EPICS = {
    "Agent Quality Scorecard": "Show finance teams how accurate and safe the AI agent is and gate go-live on objective checks (projects 02, 05).",
    "Exception Inbox": "One queue for everything automation could not finish, with a reason and a one-click fix (projects 01, 06).",
    "ERP Sync Reliability": "Invoices post to the customer's ERP exactly once, with visible status and clear failures (project 07).",
}
# epic, summary, as-a story, acceptance criteria (Given/When/Then), points, priority, labels
STORIES = [
    ("Agent Quality Scorecard", "Weekly quality score for the collections agent",
     "As a finance manager I want a weekly quality score so that I can decide whether to expand the agent.",
     "Given 50+ messages were sent, when I open the scorecard, then I see pass rate, critical-defect count and a sample of failed messages.", 5, "High", "scorecard;analytics"),
    ("Agent Quality Scorecard", "Defect breakdown with 'needs judge' flag",
     "As a quality reviewer I want defects split by type and whether rules can catch them so that I focus on tone and offers.",
     "Given a week of messages, when I view defects, then each type shows count, rule-catch rate and a 'needs judge' marker.", 3, "High", "scorecard"),
    ("Agent Quality Scorecard", "Automation vs risk setting",
     "As a finance manager I want to choose conservative, balanced or aggressive automation so that I control the risk.",
     "Given I choose a level, when invoices are processed, then STP rate and false-approve rate for that level are displayed with an explanation.", 5, "High", "scorecard;controls"),
    ("Agent Quality Scorecard", "Go-live gate",
     "As an implementation lead I want calling locked until quality thresholds are met so that unsafe agents never contact customers.",
     "Given the last 500 messages, when critical factual defects > 0 or judge kappa < 0.7, then 'Enable calling' stays disabled and the reason is shown.", 5, "Highest", "scorecard;safety"),
    ("Agent Quality Scorecard", "LLM-judge calibration set",
     "As a quality reviewer I want to label flagged messages so that the judge is calibrated against humans.",
     "Given a flagged message, when I mark it correct or incorrect, then the label is stored and agreement (kappa) is recomputed weekly.", 8, "Medium", "llm-eval"),
    ("Agent Quality Scorecard", "Hand-off on dispute",
     "As a customer who disputes an invoice I want to be handed to a person so that I am not pushed to pay.",
     "Given a dispute phrase in the reply, when the agent responds, then it hands off to a human and logs the event.", 3, "Highest", "safety"),
    ("Exception Inbox", "Unified exception queue",
     "As an AP clerk I want one queue of invoices the system could not finish so that nothing falls through.",
     "Given an invoice fails matching or capture, when I open the inbox, then it appears with type, amount, age and reason.", 5, "High", "exceptions"),
    ("Exception Inbox", "Suggested fix with one click",
     "As an AP clerk I want a suggested fix per exception so that I resolve it quickly.",
     "Given a price mismatch within policy, when I click 'Accept tolerance', then the invoice moves to approval and the decision is logged.", 8, "Medium", "exceptions;automation"),
    ("Exception Inbox", "Resolution feeds quality metrics",
     "As a product manager I want each resolution stored as a label so that automation improves over time.",
     "Given an exception is resolved, when saved, then its type, fix and time-to-resolve are stored for reporting.", 3, "Medium", "analytics"),
    ("ERP Sync Reliability", "Validate before posting",
     "As a finance manager I want invalid invoices stopped with a reason so that bad data never reaches the ERP.",
     "Given lines do not add up to the total, when submitted, then it is rejected with a reason and no ERP call is made.", 3, "High", "erp;validation"),
    ("ERP Sync Reliability", "Idempotent posting",
     "As a finance manager I want retries never to create duplicates so that the books stay correct.",
     "Given the same invoice is submitted twice, when posted, then exactly one ERP document exists.", 5, "Highest", "erp"),
    ("ERP Sync Reliability", "Retry with backoff and alerting",
     "As an integration owner I want transient errors retried and failures alerted so that I can act early.",
     "Given a timeout, when posting, then retry up to 4 times with backoff; if the failure rate exceeds 2% in an hour, an alert is sent.", 5, "High", "erp;reliability"),
    ("ERP Sync Reliability", "Sync status page",
     "As an AP clerk I want to see each invoice's sync status so that I know whether it reached the ERP.",
     "Given any invoice, when opened, then status, ERP document id and number of attempts are shown.", 3, "Medium", "erp;ux"),
]


def main():
    out = Path(__file__).parent
    problems = []
    rows = []
    for name, desc in EPICS.items():
        rows.append({"Issue Type": "Epic", "Summary": name, "Description": desc, "Priority": "High", "Epic Name": name, "Epic Link": "", "Labels": "", "Story Points": ""})
    for epic, summary, story, ac, pts, prio, labels in STORIES:
        if epic not in EPICS: problems.append(f"unknown epic for {summary}")
        if pts not in FIB: problems.append(f"story points not Fibonacci for {summary}")
        if "Given" not in ac or "then" not in ac: problems.append(f"acceptance criteria not Given/When/Then for {summary}")
        rows.append({"Issue Type": "Story", "Summary": summary, "Description": f"{story}\n\nAcceptance criteria:\n{ac}", "Priority": prio,
                     "Epic Name": "", "Epic Link": epic, "Labels": labels, "Story Points": pts})
    if problems: raise SystemExit("VALIDATION FAILED:\n" + "\n".join(problems))
    with open(out / "jira_backlog.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    total = sum(r["Story Points"] for r in rows if r["Story Points"] != "")
    by_epic = {e: sum(r["Story Points"] for r in rows if r["Epic Link"] == e) for e in EPICS}
    print(f"{len(EPICS)} epics, {len(STORIES)} stories, {total} story points; per epic: {by_epic}")


if __name__ == "__main__":
    main()
