# M0 Step 11 - UAT Execution Evidence

Date: 2026-02-18  
Status: Completed (with one open defect)

## Objective
Execute the Step 11 UAT scenario matrix with practical business prompts and capture evidence in the UAT template.

## Execution Method
1. Regression pack baseline executed first:
   - `bash impl_factory/04_automation/bench_scripts/run_step11_regression.sh`
2. UAT scenarios executed against live site `erpai_prj1` using backend runtime automation script.
3. Failed scenarios rerun with adjusted practical phrasing to distinguish prompt-phrasing issues vs product defects.

## Evidence Artifacts
1. Main UAT raw result set:
   - `impl_factory/04_automation/logs/20260218T_step11_uat_execution_raw.json`
2. Rerun evidence for failed scenarios:
   - `impl_factory/04_automation/logs/20260218T_step11_uat_reruns_raw.json`
3. Filled UAT evidence sheet:
   - `impl_factory/04_automation/uat/step11_uat_evidence_template.md`
4. Regression summary used as precondition:
   - `impl_factory/04_automation/logs/20260218T130359Z_step11_regression_summary.md`

## Results Summary
1. Initial run: `22 total`, `19 pass`, `3 fail`.
2. Rerun recovery:
   - `SAL-02`: recovered to pass with practical explicit-export prompt.
   - `CFG-02`: recovered to pass with explicit topic-cancel phrasing.
3. Remaining open defect:
   - `ENT-02` failed in initial run and reruns (`UAT-ENT-02-001`):
     ambiguous-entity option list was not surfaced in live flows tested.
4. Final UAT status after reruns: `21 pass`, `1 fail`.

## Notes
1. No ERPNext core files changed.
2. Write-capability scenarios were tested with controlled in-run flag toggling (OFF -> ON -> OFF).
3. Temporary UAT sessions and temporary ToDo records created during automation were cleaned up.
