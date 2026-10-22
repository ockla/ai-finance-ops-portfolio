# 07 - ERP connector design: canonical model, mappers, API spec and integration PRD

Integrations are where automation products win or lose: if invoices cannot flow reliably into a customer's ERP, nobody trusts the product. This project shows the product thinking and a small, tested reference implementation.

**Important:** the three ERP formats (`ERP_A`, `ERP_B`, `ERP_C`) are **simplified, illustrative schemas**, not the official schemas of any vendor.

## What is here
| File | Purpose |
|---|---|
| `erp_connector.py` | Canonical `Invoice` model; validation; mappers to three ERP-style payloads; CSV import (stand-in for an SFTP drop); idempotent posting with retry and backoff |
| `test_erp_connector.py` | 15 unit tests (all pass): validation, mapping, round trip, CSV grouping, retries, give-up, never-post-twice |
| `openapi.yaml` | API contract with idempotency key, error codes (422 validation, 429 rate limit, 502 ERP down) |
| `INTEGRATION_PRD.md` | The product requirements: goals, requirements, error handling, observability, rollout, metrics |

Run the tests: `python -m unittest -v`

## Design decisions a PM must make (and what I chose)
- **Canonical model first.** Every source (email PDF, portal, CSV) becomes one internal invoice, then maps out to each ERP. Adding a new ERP = one new mapper, not a rewrite.
- **Validate before calling the ERP.** Bad data should be stopped with a clear reason, never sent downstream (test: `rejects_invalid_without_calling_erp`).
- **Idempotency.** A retry or a duplicate must never create a second ERP document (key = vendor + invoice number + total).
- **Transient errors are retried with backoff; permanent errors are surfaced.** After 4 attempts the invoice goes to the exception inbox with the reason.
- **Reconciliation needs a round trip.** Reading back what the ERP stored (`from_erp_a`) lets us compare it with what we sent.
