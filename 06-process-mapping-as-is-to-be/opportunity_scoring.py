"""
Rank finance-ops steps by automation value vs effort and risk.
ALL INPUTS ARE ASSUMPTIONS for a mid-size company (illustrative). Replace with real customer data.

score = (monthly_volume * minutes_saved_per_item / 60) / (effort_weeks * risk)
  - monthly_volume: items per month
  - minutes_saved_per_item: handling time removed per item when automated
  - effort_weeks: rough build effort
  - risk: 1 (low) to 3 (high) cost of a mistake
"""
from pathlib import Path

STEPS = [
    # name, flow, monthly_volume, minutes_saved, effort_weeks, risk
    ("Invoice data capture (extract fields)", "P2P", 2000, 6.0, 4, 1.5),
    ("3-way matching + duplicate check", "P2P", 2000, 4.0, 5, 2.5),
    ("Approval routing + chat approvals", "P2P", 1800, 3.0, 3, 1.5),
    ("Exception triage (reason + suggested fix)", "P2P", 400, 12.0, 5, 2.0),
    ("Vendor status queries (portal / WhatsApp)", "P2P", 600, 5.0, 3, 1.0),
    ("Bank reconciliation", "P2P", 2000, 2.5, 6, 2.5),
    ("Payment reminders (automatic sequence)", "I2C", 1500, 4.0, 2, 1.0),
    ("Collections calls (voice agent)", "I2C", 500, 10.0, 8, 3.0),
    ("Cash application (match payments to invoices)", "I2C", 1500, 3.5, 5, 2.5),
    ("Dispute hand-off with context", "I2C", 150, 15.0, 3, 2.0),
]


def main():
    rows = []
    for name, flow, vol, mins, eff, risk in STEPS:
        hours_saved = vol * mins / 60
        score = hours_saved / (eff * risk)
        rows.append((score, name, flow, vol, mins, hours_saved, eff, risk))
    rows.sort(reverse=True)
    lines = ["# Automation opportunities (assumed inputs)\n",
             "| Rank | Step | Flow | Hours saved / month | Effort (weeks) | Risk | Score |", "|---|---|---|---|---|---|---|"]
    for i, (s, n, f, v, m, h, e, r) in enumerate(rows, 1):
        lines.append(f"| {i} | {n} | {f} | {h:,.0f} | {e} | {r} | {s:,.1f} |")
    lines.append("\nRead: high hours saved, low effort and low risk come first. Collections calls rank lower despite big savings per item because risk and effort are high; that is why the voice agent needs the quality scorecard (projects 02 and 05) before scaling.")
    out = Path(__file__).parent / "results"; out.mkdir(exist_ok=True)
    (out / "opportunities.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
