# Phase 1 Baseline Lock (Execution Evidence)

Date: 2026-02-18
Status: Completed
Scope: Baseline lock before iterative read-orchestrator migration

## Objective
1. Freeze current behavior and capture reproducible evidence before Phase 2.
2. Validate runtime health and FAC connectivity status.
3. Capture known failing business baseline for `Top 5 customers by revenue in last month`.

## Executed Checks
1. Regression baseline runner:
   - `bash impl_factory/04_automation/bench_scripts/run_step11_regression.sh`
2. Runtime/container health:
   - `docker compose ps`
3. Installed app check:
   - `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && bench --site erpai_prj1 list-apps'`
4. FAC probes:
   - `fac_report_list`
   - `fac_report_requirements(Sales Analytics)`
   - `fac_generate_report(Sales Analytics, Jan-2026 filters)`
   - `run_fac_report(Sales Analytics, Jan-2026 filters)`
5. Business baseline replay:
   - session flow: `Top 5 customers by revenue in last month` -> `yes`
   - captured public and debug message traces

## Artifacts
1. Regression summary:
   - `impl_factory/04_automation/logs/20260218T171128Z_step11_regression_summary.md`
2. FAC health log:
   - `impl_factory/04_automation/logs/20260218T171450Z_phase1_fac_health.log`
3. Top5 public trace:
   - `impl_factory/04_automation/logs/20260218T171450Z_phase1_top5_public.json`
4. Top5 debug trace:
   - `impl_factory/04_automation/logs/20260218T171450Z_phase1_top5_debug.json`
5. Top5 debug excerpt (quality-gate failure markers):
   - `impl_factory/04_automation/logs/20260218T171450Z_phase1_top5_debug_excerpt.txt`

## Baseline Findings (Locked)
1. Regression runner result: PASS (`compile PASS`, `contract tests PASS`, `41 tests`).
2. Runtime services are healthy (backend, websocket, queues, scheduler up).
3. `frappe_assistant_core` and `ai_assistant_ui` are installed.
4. FAC `report_list` and `generate_report` are working in this environment.
5. FAC `report_requirements` is not available via current FAC API class (`AttributeError: FAC API has no report_requirements()`).
6. `run_fac_report` works with fallback behavior and reports `requirements_error: unavailable` in debug payload.
7. Business baseline (Top5 revenue) still fails commercially:
   - asks meta-clarification (`metric/grouping`) instead of returning result,
   - `yes` continues pending option prompt,
   - debug shows `metric_alignment_mismatch` and `minimal_columns_missing` after bounded repair.

## Exit Gate for Phase 1
1. Baseline artifacts are reproducible and stored.
2. Known failure signature is captured and can be compared after Phase 2 changes.
3. Ready to proceed to Phase 2 (feature-flagged orchestrator controls).
