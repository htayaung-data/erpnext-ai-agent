# AI Assistant Baseline Snapshot

Date: 2026-02-18  
Scope: pre-stabilization baseline before production-hardening implementation

## Source Baseline
1. Runtime app source extracted from backend container into:
   - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui`
2. In-container app commit at extraction time:
   - `20131b4`
3. In-container app repo had uncommitted/untracked development changes.

## Runtime Baseline
1. Site app list includes `ai_assistant_ui`.
2. `backend` is running and serving.
3. `queue-short`, `queue-long`, and `scheduler` are restarting.
4. Crash signature:
   - `ModuleNotFoundError: No module named 'ai_assistant_ui'`

## Key Risks Identified
1. App is not consistently available across all services.
2. Deployment is not yet reproducible from project code alone.
3. App folder includes many `.bak.*` files from iterative testing and needs controlled cleanup after dependency verification.

## Immediate Next Step
M0 stabilization:
1. Make `ai_assistant_ui` available consistently to backend, websocket, workers, and scheduler.
2. Verify import/health recovery and close the restart loop.
