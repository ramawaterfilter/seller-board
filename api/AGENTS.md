# api/ — backend and finance rules (nested; adds to root AGENTS.md, never relaxes it)
- Money: Decimal only; NUMERIC(18,4) + currency in the same row; 4-dp strings on the wire; ROUND_HALF_EVEN 2 dp only at presentation; floors ROUND_CEILING; zero denominator -> null; ratios of sums.
- Signs: compat P&L lines are signed (costs negative) and summed in catalogue order; refunded principal counted once (refund_principal_in); facilitator tax nets to zero (CALC-113); unmapped fees stay in totals as Unclassified (CALC-114).
- Ledger raw-first and append-only; revisions, never overwrites; closed periods immutable; projections rebuildable.
- Migrations additive only, one per PR, downgrade tested, `alembic heads` == 1.
- Golden vectors (engineering/golden_vectors.json) are the arithmetic contract: implement to them, never edit them.
## Code Review Rules
- P0: float money, rounding before the presentation boundary, a sign flip on a compat line, a double-counted refund or fee, a destructive migration.
- P1: a money column without currency, a missing REQ-marked test, a changed or skipped golden vector, a null-to-zero coercion on stale or missing data.
