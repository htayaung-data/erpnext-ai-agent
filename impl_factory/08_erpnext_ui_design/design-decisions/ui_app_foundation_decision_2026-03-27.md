# UI App Foundation Decision

Status: accepted  
Date: 2026-03-27  
Decision owner: UI workstream

## 1. Decision

Create a dedicated Frappe app named `erp_workspace_ui` for UI-owned workspace and page implementation.

## 2. Why This Decision Was Made

The UI workstream now has enough design authority to begin implementation, but production-grade implementation should not be mixed into the existing AI Assistant app.

This decision protects:

1. ownership clarity
2. release discipline
3. branch isolation
4. cleaner installation and testing boundaries
5. future maintainability for workspace-specific UX changes

## 3. What This App Owns

`erp_workspace_ui` owns:

1. ERPNext workspace definitions for UI consoles
2. ERPNext custom pages used by workspace families
3. workspace-specific assets, styling, and front-end behavior
4. UI-side integration surfaces that consume approved assistant outputs

## 4. What This App Does Not Own

`erp_workspace_ui` does not own:

1. Qwen runtime logic
2. assistant orchestration
3. governed query planning
4. report-family reasoning logic
5. assistant state models or assistant session storage

Those remain in `ai_assistant_ui`.

## 5. First Implementation Consequence

The first console to be implemented from this app will be `Sales Console`.

The recommended implementation order remains:

1. app foundation
2. Sales Console workspace shell
3. Sales family navigation assets
4. Sales child-page assets
5. controlled AI assist embedding

## 6. Enterprise Rule

No UI implementation should be added to `ai_assistant_ui` unless it is specifically the assistant product surface.

No assistant runtime logic should be added to `erp_workspace_ui`.
