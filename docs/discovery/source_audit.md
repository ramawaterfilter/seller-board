# Source audit — draft inventory
WP-01 document artefact, prepared 2026-10-12. Register v0.3 rev 2 is authoritative.
This is an inventory of supplied source references, not a fresh provider API audit.
Existing DOC/OBS/UNVERIFIED classifications and connector-specific unknowns remain
in integration/connector_contracts.md and research/public_sources_apis.md. No live
provider connection has been made. API access and tax decisions need human review.

| ID | Connector | Mode | Release | Class | Source tags | Session verification | Linked discovery |
|---|---|---|---|---|---|---|---|
| CON-01 | Amazon SP-API (Orders, Finances, Reports, FBA Inventory, Inbound, Sales, Listings read) | read | R0 | core | S27,S28,S29,S30,S35 | Not independently verified in this session | DISC-01, DISC-02, DISC-03, DISC-04, DISC-05, DISC-06, DISC-25, DISC-26, DISC-35 (v0.3) |
| CON-02 | Amazon Ads API — spend reporting only (SP/SB/SD v3: spend by campaign, advertised product, day) | read | R1 | core | S33,S34 | Not independently verified in this session | DISC-07 |
| CON-03 | Amazon Brand Analytics / Search Terms (via Reports API) | read | — | omitted | S05,S06,S29 | OMITTED — do not implement | DISC-06 |
| CON-04 | Amazon Attribution | read | — | omitted | S12 | OMITTED — do not implement | DISC-09 |
| CON-05 | Shopify Admin GraphQL (orders, products, inventory, customers L1/L2, fulfillments) | read | R1 | core | S20,S21,S22,S23,S24,S25,S26 | Not independently verified in this session | DISC-10, DISC-29 (v0.2) |
| CON-06 | Shopify Payments payouts & balance transactions | read | R1 | core | S20 | Not independently verified in this session | DISC-11 |
| CON-07 | Other payment gateways (Razorpay/PayPal/Stripe) — fee import | read | R2 | conditional | PROP | Not independently verified in this session | DISC-12 |
| CON-08 | Google Ads — spend only | read | R1 | extended | S01,S02 | Not independently verified in this session | DISC-18 |
| CON-09 | Meta (Facebook/Instagram) Ads — spend only | read | R1 | extended | S01,S02 | Not independently verified in this session | DISC-18 |
| CON-10 | Microsoft/Bing Ads | read | — | omitted | S02 | OMITTED — do not implement | See contract section |
| CON-11 | TikTok Ads — spend only (for TikTok Shop and Shopify profit) | read | R2 | conditional | S01 | Not independently verified in this session | DISC-18 |
| CON-12 | Snapchat Ads | read | — | omitted | S01 | OMITTED — do not implement | See contract section |
| CON-13 | Pinterest Ads | read | — | omitted | S01,S02 | OMITTED — do not implement | See contract section |
| CON-14 | Taboola | read | — | omitted | S02 | OMITTED — do not implement | See contract section |
| CON-15 | Klaviyo | read | — | omitted | S02 | OMITTED — do not implement | DISC-22 |
| CON-16 | Walmart Marketplace / WFS / Walmart Connect & SEM spend (read) | read | R2 | extended | S09,S11,S14 | Not independently verified in this session | DISC-36 (v0.3) |
| CON-17 | eBay | read | R2 | extended | S11,S18 | Not independently verified in this session | DISC-37 (v0.3) |
| CON-18 | TikTok Shop | read | R2 | extended | S02 | Not independently verified in this session | DISC-38 (v0.3) |
| CON-19 | CJ Dropshipping | read | R5 | extended | S02 | Not independently verified in this session | DISC-39 (v0.3) |
| CON-20 | ShipStation (actual shipping cost) | read | R5 | extended | S02,S49 | Not independently verified in this session | See contract section |
| CON-21 | Flexport / SFN | read | R5 | extended | S02 | Not independently verified in this session | See contract section |
| CON-22 | Veeqo | read | R5 | extended | S02,OBS | Not independently verified in this session | DISC-39 (v0.3) |
| CON-23 | Private Google Sheets / CSV-XLSX URL feeds (COGS, landed cost, expenses) | read | R1 | core | S12,OBS | Not independently verified in this session | See contract section |
| CON-24 | Amazon Solicitations API (review requests) | write | — | omitted | S31 | OMITTED — do not implement | DISC-15 |
| CON-25 | Amazon Listings Items (price patch) — repricer writes | write | R4 | conditional | S32 | Not independently verified in this session | DISC-16, DISC-17, DISC-26 |
| CON-26 | Amazon Ads write (bids/budgets/negatives) | write | — | omitted | S04,S34 | OMITTED — do not implement | DISC-08 |
| CON-27 | QuickBooks / Tally export (accounting) | write | R5 | extended | OBS,S49 | Not independently verified in this session | DISC-23 |
| CON-28 | Anthropic API (optional explain layer) | read | R5 | optional | S37 | Not independently verified in this session | DISC-24 |
| CON-29 | Subscription provider (Shopify subscription app of record) | read | R2 | conditional | S20 | Not independently verified in this session | DISC-13 |
| CON-32 | Courier / 3PL fulfilment cost source (e.g., Eshopbox, courier invoices) — CSV/XLSX first, API discovery | read | R1 | conditional | OBS,PROP | Not independently verified in this session | DISC-29 (v0.2), DISC-33 (v0.2) |
| CON-33 | Internal B2B lead pipeline app (won deals → draft B2B invoices), read-only | read | R5 | conditional | PROP | Not independently verified in this session | DISC-34 (v0.2) |
| CON-30 | Amazon listing publication (write) — CONDITIONAL stub, no release | write | — | stub | S32 | Not independently verified in this session | See contract section |
| CON-31 | Fulfilment commands (MCF/WFS create/cancel) — CONDITIONAL stub, no release | write | — | stub | PROP | Not independently verified in this session | DISC-28 |
