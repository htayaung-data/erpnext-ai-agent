## Comparison Core Slice Status

Date: 2026-03-18  
Owner: AI Runtime Engineering  
Scope: status of the first approved implementation slice for `comparison`

### Decision
- Core slice complete
- Replay validated
- Manual/browser core checks validated
- One repeated-transform variant deferred as Tier-3 hardening (not a release blocker for this class core slice)

### What Is Complete
The approved first slice is complete for:

1. deterministic same-period side-by-side comparison for:
   - territory revenue
   - customer revenue
   - supplier purchase amount
   - item revenue/sales
2. deterministic monthly comparison for:
   - explicit month-vs-month comparison
   - bounded month-over-month comparison
3. approved first-slice follow-up behaviors:
   - same-period comparison scale follow-up (`Show in Million`)
   - monthly comparison scale follow-up
   - month-over-month scale follow-up
4. approved clarification / unsupported boundaries:
   - missing business measure
   - weekly comparison unsupported
   - quarterly comparison unsupported

### Replay Evidence
Authoritative class-suite result:

1. [20260317T200348Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260317T200348Z_phase6_manifest_uat_raw_v3.json)
2. summary:
   - total: `13`
   - passed: `13`
   - failed: `0`
   - first-run pass rate: `1.0`

Targeted post-hardening gates:

1. [20260318T111850Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260318T111850Z_phase6_manifest_uat_raw_v3.json) (`CMPC-12`) pass
2. [20260318T111851Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260318T111851Z_phase6_manifest_uat_raw_v3.json) (`CMPC-13`) pass
3. [20260318T111854Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260318T111854Z_phase6_manifest_uat_raw_v3.json) (`CMPC-11`) pass
4. [20260318T111921Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260318T111921Z_phase6_manifest_uat_raw_v3.json) (`CMPC-10`) pass
5. [20260318T175919Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260318T175919Z_phase6_manifest_uat_raw_v3.json) (`CMPC-08`) pass
6. [20260318T175920Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260318T175920Z_phase6_manifest_uat_raw_v3.json) (`CMPC-09`) pass

Regression suites already held green during comparison expansion:

1. `core_read`: `114/114` pass
2. `multiturn_context`: `81/81` pass

### Manual/Browser Evidence

1. [step30_comparison_manual_execution_evidence_2026-03-18.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step30_comparison_manual_execution_evidence_2026-03-18.md)

### What Is Deferred (Tier-3 Hardening, Non-Blocker For Core Slice)

1. repeated `Show in Million` after an already-scaled monthly/MoM comparison is not yet idempotent
2. current fallback shape for that repeated follow-up drifts to a generic KPI total view

### Current Product Meaning

1. `comparison` core class is complete and green for the approved first-slice business behaviors
2. same-period and monthly comparison presentation now meet the approved comparison shape
3. one repeated-transform follow-up variant is intentionally deferred and tracked

### Next-Step Rule

After this core freeze:

1. do not reopen repeated-transform hardening informally
2. if prioritized, activate a bounded hardening candidate for comparison follow-up idempotency
3. otherwise move to Phase 3 closure work
