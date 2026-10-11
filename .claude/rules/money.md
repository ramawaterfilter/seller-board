# Money rules (spec §3, single source of truth)

- Python: `decimal.Decimal` only. Never `float` for amounts, rates, quantities that multiply money.
- Storage: `NUMERIC(18,4) amount` + `currency CHAR(3)` in the same row. Never a money column without currency. FX rates `NUMERIC(20,10)`.
- Wire (API JSON): string with 4 decimal places, e.g. `"1234.5000"`, plus `currency`. Never a JSON number.
- Presentation: `ROUND_HALF_EVEN` to the currency minor unit (2 dp) at render time only (`<Money>` component / `format_money`).
- Floors and minimums (price floor, reorder carton, MOQ): `ROUND_CEILING` so a floor is never rounded below itself (GV-040).
- Internal arithmetic exact; quantize only at the storage/presentation boundary.
- Zero or null denominator -> `null`, never `0`, never an exception (GV-019, GV-054, GV-060). Aggregate ratios are ratios of sums (GV-017).
- Converted amounts are never stored in event tables; projections store the `currency_rate.id` used.
- Unknown fee codes go to `Unclassified` and stay in totals (GV-011); Walmart / eBay / TikTok Shop fee types map through the versioned `cost.channel_fee_map` with Σ mapped == Σ source (CALC-114, GV-154).
- Signs: compat P&L lines are signed (costs negative); marketplace-facilitator tax (`SALES_TAX_MF`, `MF_VAT`) collected and withheld net to zero and never enter Sales or the tax line (CALC-113, GV-152; else `MF_TAX_NOT_NETTED`); a missing regime -> tax line `null` + `REGIME_MISSING`, never 0.
- Ad spend per ad account comes from exactly one `spend_source` (connector | settlement); the other is an excluded memo amount (CALC-079, GV-155).
- Missing COGS -> `null` + `cogs_missing=true` (GV-018).

Rejected patterns: `float(amount)`, `round(x, 2)` inside domain code, `amount: number` in TS exports, `Numeric` without a sibling `currency`.
