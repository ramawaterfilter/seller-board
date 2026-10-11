# Error envelope and status codes

Every non-2xx response body is exactly:

```json
{"error": {"code": "PERIOD_CLOSED", "message": "human readable", "details": {}, "trace_id": "…"}}
```

- `code`: stable UPPER_SNAKE string; add new codes to `api/src/app/errors.py` and the OpenAPI enum; never rename.
- `details`: an object (may be empty); field errors go under `details.fields`.
- `trace_id`: OpenTelemetry trace id, also stored on `platform.audit_log`, `ing.sync_job`, `auto.automation_execution`.
- Status mapping: 400 validation, 401 unauthenticated, 403 forbidden (`MAKER_CHECKER_VIOLATION`, `SECOND_PERSON_REQUIRED`, `DEMO_READ_ONLY`), 404 not found or out of scope (cross-workspace / out-of-market reads return 404, not 403), 409 `REVISION_CONFLICT` on stale `If-Match`, 412 `WRITE_PATH_DISABLED` when the per-path flag is false or a kill switch is engaged, 422 domain rule (`PERIOD_CLOSED`, `FLOOR_VIOLATION`, `REGIME_MISSING`; B2B numbering `DOC_NO_REQUIRED`, `DOC_NO_INVALID`, `DOC_NO_NOT_ALLOWED`, `DOC_SERIES_MISSING`; 409 `DOC_NO_DUPLICATE`), 429 rate/budget (`EXPLAIN_BUDGET`), 500 with generic message only.
- Never leak provider error bodies, SQL, stack traces or secrets in `message`.
- Alert codes match runbooks: `CONNECTOR_REVOKED` (RB-01), `SYNC_DEAD` (RB-02), `SETTLEMENT_VARIANCE` (RB-03), `UNKNOWN_FEE_CODE` / `UNCLASSIFIED_FEE` (RB-04), `SOURCE_STALE` (RB-05), `kill_switch_engaged` (RB-06). Ad alerts are spend-only: `AD_SPEND_MISSING`, `AD_SPEND_SPIKE` (no PPC recommendation codes).
- Tax-regime codes (CALC-113, spec §3.15) use the canonical enum `VAT_SELLER | GST_SELLER | CONSUMPTION_TAX | SALES_TAX_MF | MF_VAT` and the flags `REGIME_MISSING` (also the 422 code), `REGIME_MISMATCH`, `MF_TAX_NOT_NETTED`; no other spelling (e.g. `TAX_REGIME_*`, `seller_vat`) exists.
