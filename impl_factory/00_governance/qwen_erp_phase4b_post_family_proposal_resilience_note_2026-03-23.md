# Qwen ERP Phase 4B Post-Family Proposal Resilience Note (2026-03-23)

Status: completed  
Scope: post-4B resilience hardening after family evaluation exposed one remaining governed compile gap  
Goal: keep Phase 4B aligned with enterprise contracts while closing the last unstable family-routing case without drifting into query-specific hacks.

## 1. Why This Hardening Was Needed

After the Phase 4B family evaluation framework was implemented, the governed baseline improved materially but still showed one remaining failure:

- `Top 5 customers by revenue`

The failure was not architectural drift and not a runtime crash.

It was a governed compile miss:

1. the request was reaching the correct report surface (`Sales Analytics`)
2. but ranking queries could still arrive with no governed dimension/metric anchors
3. the compiler then correctly chose `clarify` rather than unsafe execution

That meant the remaining weakness was in proposal/fallback resilience, not in the compiler boundary.

## 2. What Was Changed

The hardening added two enterprise-safe controls.

### 2.1 Governed Request Defaults

Family-level deterministic defaults were added for the proposal contract when the model or deterministic fallback leaves a governed family underspecified.

The defaults now cover:

1. `ranked_entities`
2. `trend_analysis`
3. `product_performance`
4. `financial_summary`
5. `inventory_summary`

Examples of governed defaults:

- sales ranking:
  - default dimension -> `Customer`
  - default metric -> `Revenue`
- sales trend:
  - default metric -> `Revenue`
  - default time scope -> `current_fiscal_year_to_date`
- aging summary:
  - default metric -> `Outstanding`
  - default time scope -> `as_of_today`
- product performance:
  - default dimension -> `Item Code`
  - default metric -> `Gross Profit`

These are family-level defaults, not phrase-specific answer hacks.

### 2.2 Deterministic Family-Surface Fallback

When runtime proposal generation is unavailable, invalid, or otherwise unusable, the ERP layer now builds a governed interpretation from the reduced family tool surface.

That fallback:

1. respects governed family routing
2. selects governed capability/report candidates
3. applies family-level default dimensions/metrics/time scope
4. still passes through compiler enforcement and validation

So the system remains:

- `Qwen-Agent proposes`
- `compiler enforces`
- `validator confirms`

even when proposal resilience mechanisms are engaged.

## 3. Enterprise Assessment

This hardening is aligned with enterprise standards because:

1. it does not weaken compiler clarify/execute policy
2. it does not bypass semantic validation
3. it does not add report-by-report prompt hacks
4. it strengthens family-level determinism in the exact layer that should own it

The last open family gap was therefore solved as:

- semantic family defaulting
- governed fallback hardening

not as:

- keyword patching
- direct answer templating
- uncontrolled model freedom

## 4. Verification Result

The full governed family evaluation suite was rerun after the hardening.

Result:

1. case count: `11`
2. passed: `11`
3. failed: `0`

This means:

- all core governed families now pass
- extended financial statement cases pass
- extended governed execute cases pass

Important measured outcome:

- the remaining failure was resolved without introducing new family regressions

## 5. Current Posture

Phase 4B now has:

1. governed family registry
2. normalized adapters for core business families
3. compiler-approved composite execution
4. canonical family rendering
5. reduced family tool surface
6. family-level evaluation framework
7. green governed family baseline (`11/11`)

The next work should now move to:

1. broader family-package expansion
2. larger evaluation sets per family
3. continued latency reduction on heavier governed families
4. later multilingual/Burmese and OCR-ready normalization layers
