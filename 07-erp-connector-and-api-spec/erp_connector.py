"""
ERP connector sketch: one canonical invoice model, mappers to three SIMPLIFIED ERP payload styles,
validation, idempotency (no double posting) and retry with backoff.

The three target formats (ERP_A, ERP_B, ERP_C) are simplified, illustrative schemas inspired by common
patterns in accounting/ERP APIs. They are NOT the official schemas of any vendor. The point is the
design a product manager must specify: a canonical model, field mapping, validation rules, idempotency,
error handling and observability.
"""
from __future__ import annotations
import csv, hashlib, io, time
from dataclasses import dataclass, field
from datetime import date
from typing import Callable

CURRENCIES = {"INR", "USD", "SGD", "IDR", "EUR"}
TOLERANCE = 0.01  # totals must reconcile within 1 currency unit


@dataclass
class Line:
    description: str
    quantity: float
    unit_price: float

    @property
    def amount(self) -> float:
        return round(self.quantity * self.unit_price, 2)


@dataclass
class Invoice:
    invoice_no: str
    vendor: str
    invoice_date: date
    currency: str
    lines: list[Line]
    total: float
    po_ref: str | None = None

    def idempotency_key(self) -> str:
        """Same vendor + invoice number + total always produces the same key, so a retry never posts twice."""
        raw = f"{self.vendor.strip().lower()}|{self.invoice_no.strip().upper()}|{self.total:.2f}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


class ValidationError(Exception):
    pass


def validate(inv: Invoice) -> list[str]:
    """Return a list of problems (empty list = OK). Validate BEFORE calling any ERP."""
    errs = []
    if not inv.invoice_no.strip(): errs.append("invoice_no is required")
    if not inv.vendor.strip(): errs.append("vendor is required")
    if inv.currency not in CURRENCIES: errs.append(f"unsupported currency {inv.currency}")
    if not inv.lines: errs.append("at least one line is required")
    if any(l.quantity <= 0 or l.unit_price < 0 for l in inv.lines): errs.append("line quantity must be > 0 and price >= 0")
    if inv.lines and abs(sum(l.amount for l in inv.lines) - inv.total) > TOLERANCE:
        errs.append("line amounts do not add up to total")
    if inv.invoice_date > date.today(): errs.append("invoice_date is in the future")
    return errs


# ---------------- mappers: canonical -> ERP payload (simplified, illustrative) ----------------
def to_erp_a(inv: Invoice) -> dict:
    return {"tranId": inv.invoice_no, "entity": inv.vendor, "tranDate": inv.invoice_date.isoformat(), "currency": inv.currency,
            "lineItems": [{"item": l.description, "quantity": l.quantity, "rate": l.unit_price, "amount": l.amount} for l in inv.lines],
            "total": inv.total, "createdFrom": inv.po_ref}


def to_erp_b(inv: Invoice) -> dict:
    return {"InvoiceNumber": inv.invoice_no, "Contact": {"Name": inv.vendor}, "Date": inv.invoice_date.strftime("%Y-%m-%d"),
            "CurrencyCode": inv.currency, "Reference": inv.po_ref,
            "LineItems": [{"Description": l.description, "Quantity": l.quantity, "UnitAmount": l.unit_price, "LineAmount": l.amount} for l in inv.lines],
            "Total": inv.total}


def to_erp_c(inv: Invoice) -> dict:
    return {"DocNumber": inv.invoice_no, "VendorRef": {"name": inv.vendor}, "TxnDate": inv.invoice_date.isoformat(), "CurrencyRef": inv.currency,
            "PrivateNote": inv.po_ref or "",
            "Line": [{"Description": l.description, "Qty": l.quantity, "UnitPrice": l.unit_price, "Amount": l.amount} for l in inv.lines],
            "TotalAmt": inv.total}


MAPPERS: dict[str, Callable[[Invoice], dict]] = {"ERP_A": to_erp_a, "ERP_B": to_erp_b, "ERP_C": to_erp_c}


def from_erp_a(p: dict) -> Invoice:
    """Round trip back to canonical (used for reconciliation: what did the ERP actually store?)."""
    return Invoice(p["tranId"], p["entity"], date.fromisoformat(p["tranDate"]), p["currency"],
                   [Line(i["item"], i["quantity"], i["rate"]) for i in p["lineItems"]], p["total"], p.get("createdFrom"))


# ---------------- import from CSV (stand-in for an SFTP drop) ----------------
def from_csv(text: str) -> list[Invoice]:
    """CSV columns: invoice_no,vendor,invoice_date,currency,po_ref,description,quantity,unit_price (one row per line)."""
    grouped: dict[str, dict] = {}
    for row in csv.DictReader(io.StringIO(text)):
        g = grouped.setdefault(row["invoice_no"], dict(vendor=row["vendor"], date=row["invoice_date"], cur=row["currency"], po=row.get("po_ref") or None, lines=[]))
        g["lines"].append(Line(row["description"], float(row["quantity"]), float(row["unit_price"])))
    out = []
    for no, g in grouped.items():
        total = round(sum(l.amount for l in g["lines"]), 2)
        out.append(Invoice(no, g["vendor"], date.fromisoformat(g["date"]), g["cur"], g["lines"], total, g["po"]))
    return out


# ---------------- posting with idempotency + retry ----------------
@dataclass
class SyncResult:
    status: str                      # "posted" | "duplicate_skipped" | "rejected" | "failed"
    detail: str = ""
    attempts: int = 0


@dataclass
class ErpClient:
    """Stand-in for a remote ERP API. `fail_first_n` simulates transient errors (timeouts, 429, 5xx)."""
    fail_first_n: int = 0
    stored: dict = field(default_factory=dict)
    calls: int = 0

    def post_invoice(self, payload: dict, idempotency_key: str) -> str:
        self.calls += 1
        if self.calls <= self.fail_first_n:
            raise TimeoutError("simulated transient ERP error")
        if idempotency_key in self.stored:
            return self.stored[idempotency_key]["id"]
        rid = f"ERP-{len(self.stored) + 1:05d}"
        self.stored[idempotency_key] = {"id": rid, "payload": payload}
        return rid


def sync_invoice(inv: Invoice, target: str, client: ErpClient, max_attempts: int = 4, base_delay: float = 0.0) -> SyncResult:
    problems = validate(inv)
    if problems:
        return SyncResult("rejected", "; ".join(problems))
    key = inv.idempotency_key()
    if key in client.stored:
        return SyncResult("duplicate_skipped", f"already posted as {client.stored[key]['id']}")
    payload = MAPPERS[target](inv)
    for attempt in range(1, max_attempts + 1):
        try:
            rid = client.post_invoice(payload, key)
            return SyncResult("posted", rid, attempt)
        except TimeoutError as e:
            if attempt == max_attempts:
                return SyncResult("failed", f"gave up after {attempt} attempts: {e}", attempt)
            time.sleep(base_delay * (2 ** (attempt - 1)))   # exponential backoff (0 in tests)
    return SyncResult("failed", "unreachable", max_attempts)
