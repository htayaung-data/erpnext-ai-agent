# M0 Step 2 - Runtime Stabilization Execution Log

Date: 2026-02-18  
Status: Completed

## Objective
Recover Python service stability by making `ai_assistant_ui` importable in all runtime services and removing worker/scheduler restart loops.

## Changes Applied
File: `compose.yaml`

1. Mounted managed app source into Python services:
   - `configurator`
   - `backend`
   - `websocket`
   - `queue-short`
   - `queue-long`
   - `scheduler`
   - `create-site`

2. Added install step for new-site bootstrap:
   - `--install-app ai_assistant_ui` in `create-site`.

3. Fixed command wiring for reproducibility:
   - Replaced broken `entrypoint + command: >` behavior in `configurator` and `create-site` with explicit `bash -lc` command arrays and `set -euo pipefail`.

4. Added `PYTHONPATH` for Python app import resolution:
   - `PYTHONPATH=/home/frappe/frappe-bench/apps/ai_assistant_ui`
   - Applied to `configurator`, `backend`, `websocket`, `queue-short`, `queue-long`, `scheduler`, `create-site`.

## Verification Evidence
1. `docker compose config --quiet` passed after changes.
2. `docker compose up configurator` succeeded with:
   - `OK: common_site_config.json written`
3. Runtime status stabilized:
   - `backend`, `websocket`, `queue-short`, `queue-long`, `scheduler` all `Up`.
4. Logs check:
   - No `ModuleNotFoundError: No module named 'ai_assistant_ui'` in worker/scheduler startup logs.
5. Import checks:
   - `docker compose exec backend python -c "import ai_assistant_ui"` passed.
   - `docker compose exec queue-short python -c "import ai_assistant_ui"` passed.
   - `docker compose exec scheduler python -c "import ai_assistant_ui"` passed.
6. Site app list check:
   - `bench --site erpai_prj1 list-apps` includes `ai_assistant_ui`.

## Notes
1. `docker compose` warns about orphan `caddy` when commands are run without `compose.caddy.yaml`; this did not block stabilization.
2. Further hardening and cleanup continue in next steps (contract compliance + code cleanup + tests).
