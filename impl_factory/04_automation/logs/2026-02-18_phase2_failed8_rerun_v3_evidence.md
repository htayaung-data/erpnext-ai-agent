# Phase 2 Canary Failed-8 Rerun Evidence (v3)

Date: 2026-02-18  
Site: `erpai_prj1`  
User: `Administrator`

## Scope
Replayed the 8 scenarios that previously failed in Phase 2 canary rerun:
`FIN-02`, `SAL-01`, `SAL-02`, `STK-02`, `HR-01`, `OPS-01`, `ENT-01`, `ENT-02`.

## Result Summary
- Total: 8
- Passed: 8
- Failed: 0

Raw artifact:
- `impl_factory/04_automation/logs/20260218T183205Z_phase2_failed8_rerun_v3_raw.json`

## Notes
- `STK-02` was replayed with deterministic context seeding (`Show stock balance in warehouse mmob` then choose option `1`) before sending `Show stock balance in the same warehouse`.
- Entity scenarios now show contract-aligned behavior:
  - `ENT-01`: explicit no-match refine prompt.
  - `ENT-02`: explicit ambiguity prompt with options.
- This rerun supersedes the intermediate `v2` extraction artifact (`20260218T182718Z_phase2_failed8_rerun_v2_raw.json`) which used an incomplete extraction approach for pending-state fields.
