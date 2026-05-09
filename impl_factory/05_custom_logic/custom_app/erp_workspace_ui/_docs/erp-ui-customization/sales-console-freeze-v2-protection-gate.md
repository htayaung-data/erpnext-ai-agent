# Sales Console Freeze v2 Protection Gate

Date: 2026-05-09
Status: Mandatory release gate
Applies to: `sales-console-freeze-v2`

## Why This Gate Exists

Sales Console is the frozen premium reference workspace. Future shared-core, Procurement, and new workspace work must not silently damage Sales route lifecycle, list and report shells, detail boundaries, governed native forms, visual stability, or route/action governance.

This gate is machine-runnable. Documentation and visual confidence are not enough.

## When It Is Mandatory

Run this gate before accepting any change that touches:

- shared CSS or shared workspace runtime
- app boot, route lifecycle, sidebar, list shell, report shell, or child/detail shell
- workspace registry or governance manifest
- Sales backend adapter files
- Sales page controllers
- managed Sales form assets
- native exception policy or shared workspace contracts
- Procurement or future workspace work that could exercise shared core

No shared-core, Procurement, or new workspace change is acceptable unless this gate passes after the change.

Live alignment must not happen until this gate passes in source. If the gate fails only because live is stale, prove source passes first and request a separate controlled live alignment.

## Required Environment Variables

Set these variables before running the gate. Do not print or hardcode passwords.

```bash
export ERPW_BASE_URL="https://meet.erpbosai.com"
export ERPW_MANAGER_USERNAME="<sales-manager-user>"
export ERPW_MANAGER_PASSWORD="<sales-manager-password>"
export ERPW_USER_USERNAME="<sales-user>"
export ERPW_USER_PASSWORD="<sales-user-password>"
```

Optional:

```bash
export ERPW_SALES_FREEZE_ARTIFACT_ROOT="/path/to/artifacts/sales-freeze-protection-YYYYMMDDTHHMMSSZ"
```

## Exact Command

Run from the clean source custom app root:

```bash
cd /home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui
npm --prefix ui_smoke run test:sales-freeze-protection
```

The npm command calls:

```bash
ui_smoke/run_sales_freeze_protection_gate.sh
```

Browser checks use only the existing Docker Playwright runner:

```bash
ui_smoke/run_playwright_docker.sh
```

## Artifact Location

Each run writes a unique artifact root:

```text
ui_smoke/artifacts/sales-freeze-protection-YYYYMMDDTHHMMSSZ/
```

If `ui_smoke/artifacts/` is not writable because previous Docker runs created root-owned artifacts, the gate falls back to:

```text
/tmp/sales-freeze-protection-YYYYMMDDTHHMMSSZ/
```

The gate writes child folders for each smoke and a final summary:

```text
sales-freeze-protection-summary.json
```

The summary includes timestamp, git branch, git commit, command list, pass/fail status, artifact paths, and the failed command if any.

The summary also records the exact source state that was validated:

- HEAD commit
- branch
- `git status --short --branch`
- whether the working tree was dirty
- changed tracked files from `git diff --name-status HEAD`
- untracked files from `git ls-files --others --exclude-standard`

The gate can validate uncommitted work. When it does, the summary must make that explicit through `working_tree_dirty`, `changed_files_name_status`, and `untracked_files`. This is intentional evidence, not a clean-release claim.

Recommended final practice for a major freeze or protection baseline:

1. Run the gate before commit to prove the candidate diff.
2. Commit only the approved files.
3. Run the gate again after commit to prove the committed source state.
4. Push only after the post-commit gate passes.

## What The Gate Runs

Source checks:

- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- `node --check` for Sales and shared JS files that can affect Sales
- `git diff --check HEAD`

The source checks write real logs into the artifact root:

- `python-compileall.log`
- `python-unit-discovery.log`
- `node-check.log`
- `git-diff-check.log`

Browser smoke checks:

- Sales route lifecycle: first landing, direct route load, sidebar navigation, no stacking, refresh, back/forward
- Sales action cards: visible Overview actions are classified and do not no-op or leak
- Sales worklists: directory/worklist shell, filters, autocomplete, AJAX Apply/Reset/Refresh
- Sales detail boundary: Customer/Item detail, customer editor, and managed document boundaries
- Sales report family: Sales Analytics, Sales Order Analysis, Trend Analysis, Lost Quotations, Collections Status, Item-wise Sales History
- Sales native leakage: productized pages do not expose unclassified native ERPNext paths or forbidden mutations
- Sales visual stability: premium layout, no focus shrink, no obvious overflow
- Sales Order Analysis for Sales Manager and Sales User

## Static Watchlist

Use this helper to see whether a diff touches files that require the full gate:

```bash
npm --prefix ui_smoke run test:sales-freeze-watchlist
```

The watchlist includes:

- `erp_workspace_ui/public/css/erp_workspace_ui.css`
- `erp_workspace_ui/public/js/erp_workspace_ui_boot.js`
- `erp_workspace_ui/public/js/runtime/console/*`
- `erp_workspace_ui/public/js/runtime/list_page/list_page_shell.js`
- `erp_workspace_ui/public/js/runtime/report_page/report_page_shell.js`
- `erp_workspace_ui/public/js/runtime/child_page/*`
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- `erp_workspace_ui/workspace_governance_manifest.py`
- Sales backend modules
- Sales page controllers
- managed Sales form assets

The watchlist helper is a reminder, not a replacement for the full gate.

## If The Gate Fails

Stop immediately.

Use the summary JSON to identify the failed command and artifact path. Do not commit or push the change. Do not live-align. If the failure is a true Sales regression, repair the source and rerun the full gate. If the failure is caused by stale live deployment while source passes, document the source pass and request controlled live alignment separately.

Procurement should not be repaired inside a Sales freeze protection task unless the owner explicitly approves that scope.
