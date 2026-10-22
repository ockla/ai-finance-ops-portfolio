# 08 - Jira-ready backlog and customer discovery kit

- `make_backlog.py` generates `jira_backlog.csv` (3 epics, 13 stories, 61 story points) and validates it: stories belong to an epic, story points are Fibonacci, every story has Given/When/Then acceptance criteria. The CSV imports into Jira (map Summary, Description, Priority, Labels, Story Points, Epic Name, Epic Link).
- `discovery_kit.md` is the research method: goals, screener, interview guide, pain-quantification table, hypotheses, synthesis template. **It contains no invented findings.**

The backlog turns the product bets from projects 02, 05, 06 and 07 into work engineers can pick up.

Run: `python make_backlog.py`
