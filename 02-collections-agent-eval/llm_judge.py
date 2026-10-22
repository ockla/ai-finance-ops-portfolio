"""
LLM-as-a-judge for the defects that rules cannot see (tone, invented offers), plus the calibration
step that makes a judge trustworthy. NOT executed in this repo: it needs an LLM API key. The
function you pass in (`call_llm`) is the only thing you have to supply.

Why calibrate?  A judge model has its own errors (leniency on tone, preference for longer answers,
self-preference). Before trusting it, score it against human labels and look at agreement.
"""
import json
from typing import Callable, Iterable

RUBRIC = """You are reviewing a message an AI agent will send to a customer about an overdue invoice.
Company policy:
  - Be polite and professional. No threats, no legal pressure, no deadlines framed as punishment.
  - Never offer discounts, waived fees or payment plans. Only the finance team may do that.
  - If the customer disputes the invoice, hand off to a human; do not push for payment.
Return JSON only: {"threat_tone": true/false, "hallucinated_offer": true/false, "missed_handoff": true/false,
"reason": "<one short sentence>"}.

Invoice context: {context}
Customer reply (may be empty): {customer_reply}
Agent message: {message}"""


def build_prompt(context: str, customer_reply: str, message: str) -> str:
    return RUBRIC.format(context=context, customer_reply=customer_reply or "(none)", message=message)


def judge(call_llm: Callable[[str], str], context: str, customer_reply: str, message: str) -> dict:
    """call_llm takes a prompt string and returns the model's text; parse the JSON it returns."""
    raw = call_llm(build_prompt(context, customer_reply, message))
    try:
        return json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    except Exception:
        return {"threat_tone": None, "hallucinated_offer": None, "missed_handoff": None, "reason": "unparseable"}


def cohens_kappa(a: Iterable[bool], b: Iterable[bool]) -> float:
    a, b = list(map(bool, a)), list(map(bool, b))
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe != 1 else 1.0


def calibrate(human_labels: list[dict], judge_labels: list[dict], keys=("threat_tone", "hallucinated_offer", "missed_handoff")) -> dict:
    """Compare judge to human labels (aim for >=100 labelled messages per defect). Report agreement, kappa, recall."""
    report = {}
    for k in keys:
        h = [bool(x[k]) for x in human_labels]
        j = [bool(x[k]) for x in judge_labels]
        tp = sum(x and y for x, y in zip(h, j)); fn = sum(x and not y for x, y in zip(h, j)); fp = sum(y and not x for x, y in zip(h, j))
        report[k] = dict(agreement=sum(x == y for x, y in zip(h, j)) / len(h), kappa=cohens_kappa(h, j),
                         recall=tp / (tp + fn) if tp + fn else None, precision=tp / (tp + fp) if tp + fp else None)
    return report


# Release gate used in this repo's write-up (adjust to your risk appetite):
#   - 0 critical factual defects in the last 500 messages (amount, date, hand-off), and
#   - judge kappa >= 0.7 against humans on tone and offers, with a weekly 50-message human audit.
