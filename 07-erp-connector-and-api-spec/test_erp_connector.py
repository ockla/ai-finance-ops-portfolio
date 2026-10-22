import unittest
from datetime import date, timedelta
from erp_connector import (Invoice, Line, validate, MAPPERS, from_erp_a, from_csv, sync_invoice, ErpClient)


def good_invoice(no="INV-1", total=None):
    lines = [Line("Packaging", 10, 25.0), Line("Freight", 1, 50.0)]
    return Invoice(no, "Apex Logistics Pvt Ltd", date(2026, 9, 1), "INR", lines, total if total is not None else 300.0, "PO-77")


class TestValidation(unittest.TestCase):
    def test_valid_invoice_has_no_errors(self): self.assertEqual(validate(good_invoice()), [])
    def test_totals_must_reconcile(self): self.assertIn("line amounts do not add up to total", validate(good_invoice(total=999)))
    def test_unsupported_currency(self):
        inv = good_invoice(); inv.currency = "XYZ"; self.assertTrue(any("currency" in e for e in validate(inv)))
    def test_future_date_rejected(self):
        inv = good_invoice(); inv.invoice_date = date.today() + timedelta(days=3); self.assertTrue(any("future" in e for e in validate(inv)))
    def test_missing_vendor(self):
        inv = good_invoice(); inv.vendor = " "; self.assertIn("vendor is required", validate(inv))
    def test_zero_quantity_rejected(self):
        inv = good_invoice(); inv.lines[0].quantity = 0; self.assertTrue(any("quantity" in e for e in validate(inv)))


class TestMapping(unittest.TestCase):
    def test_all_targets_carry_total_and_number(self):
        inv = good_invoice()
        self.assertEqual(MAPPERS["ERP_A"](inv)["total"], 300.0)
        self.assertEqual(MAPPERS["ERP_B"](inv)["Total"], 300.0)
        self.assertEqual(MAPPERS["ERP_C"](inv)["TotalAmt"], 300.0)
        self.assertEqual(MAPPERS["ERP_B"](inv)["InvoiceNumber"], "INV-1")
    def test_round_trip_erp_a(self):
        inv = good_invoice(); back = from_erp_a(MAPPERS["ERP_A"](inv))
        self.assertEqual((back.invoice_no, back.total, len(back.lines)), (inv.invoice_no, inv.total, 2))


class TestCsvImport(unittest.TestCase):
    CSV = ("invoice_no,vendor,invoice_date,currency,po_ref,description,quantity,unit_price\n"
           "INV-9,Delta Foods LLP,2026-08-15,INR,PO-1,Rice,100,40\n"
           "INV-9,Delta Foods LLP,2026-08-15,INR,PO-1,Oil,20,150\n"
           "INV-10,Delta Foods LLP,2026-08-16,INR,,Sugar,10,45\n")
    def test_groups_lines_and_computes_totals(self):
        invs = {i.invoice_no: i for i in from_csv(self.CSV)}
        self.assertEqual(len(invs), 2); self.assertEqual(invs["INV-9"].total, 7000.0); self.assertIsNone(invs["INV-10"].po_ref)


class TestSync(unittest.TestCase):
    def test_posts_valid_invoice(self):
        r = sync_invoice(good_invoice(), "ERP_A", ErpClient()); self.assertEqual((r.status, r.attempts), ("posted", 1))
    def test_rejects_invalid_without_calling_erp(self):
        c = ErpClient(); r = sync_invoice(good_invoice(total=1), "ERP_A", c); self.assertEqual(r.status, "rejected"); self.assertEqual(c.calls, 0)
    def test_retries_transient_errors_then_succeeds(self):
        c = ErpClient(fail_first_n=2); r = sync_invoice(good_invoice(), "ERP_C", c); self.assertEqual((r.status, r.attempts), ("posted", 3))
    def test_gives_up_after_max_attempts(self):
        c = ErpClient(fail_first_n=10); r = sync_invoice(good_invoice(), "ERP_B", c, max_attempts=3); self.assertEqual((r.status, r.attempts), ("failed", 3))
    def test_never_posts_twice(self):
        c = ErpClient(); a = sync_invoice(good_invoice(), "ERP_A", c); b = sync_invoice(good_invoice(), "ERP_A", c)
        self.assertEqual((a.status, b.status, len(c.stored)), ("posted", "duplicate_skipped", 1))
    def test_idempotency_key_ignores_case_and_spacing(self):
        a = good_invoice("inv-1"); b = good_invoice("INV-1"); b.vendor = "  apex logistics pvt ltd "
        self.assertEqual(a.idempotency_key(), b.idempotency_key())


if __name__ == "__main__":
    unittest.main()
