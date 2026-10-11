# Timestamp and period rules

- Postgres: `timestamptz` only; never `timestamp without time zone`, never `date` for instants.
- Python: aware `datetime` only (`ruff` DTZ rules are errors). `datetime.now(tz=UTC)`; never `datetime.now()` / `utcnow()`.
- Wire: ISO-8601 with offset (`2026-09-10T00:00:00+05:30`). Dates that are business days (period keys) are `YYYY-MM-DD` strings with the store timezone implied by the store record.
- Store timezone (`ws.store.timezone`, IANA) drives Today / Yesterday / MTD; boundaries are computed server-side, never in the browser.
- Periods (`ws.period`) are materialized per store timezone; a closed period is immutable; late corrections post to the earliest open period with `original_period_key` lineage (GV-025); `close_hash` detects drift.
- Provider timestamps are stored as received in `ing.raw_payload` and normalized once in `ledger.*`.
- UI: render only through `<When value tz>`; never `toLocaleString()` without an explicit timezone.
