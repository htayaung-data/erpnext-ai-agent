# Qwen ERP Parallel Workstream Governance (2026-03-27)

## Purpose

This note defines how the repository is separated into parallel workstreams so AI Assistant engineering and ERPNext UI design can continue without unnecessary conflicts.

The goal is to:

1. keep `main` clean as the controlled integration branch
2. let AI Assistant engineering continue without blocking UI design work
3. reduce accidental file mixing and commit contamination
4. make branch ownership and coordination boundaries explicit

## Branch Strategy

Repository branches are assigned as follows:

1. `main`
   - clean integration branch only
   - no direct feature development
   - merges happen intentionally after review and verification
2. `feature/ai-assistant`
   - active AI Assistant implementation and hardening
3. `feature/erpnext-ui-design`
   - ERPNext UI design stream

## Worktree Strategy

Each active branch should operate in its own local worktree.

Active layout:

1. AI Assistant worktree
   - branch: `feature/ai-assistant`
   - path: `/home/deploy/erp-projects/erpai_project1`
2. UI design worktree
   - branch: `feature/erpnext-ui-design`
   - path: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
3. clean integration worktree
   - branch: `main`
   - path: `/home/deploy/erp-projects/erpai_project1_main_integration`

Operational rule:

1. do not use one worktree for both streams
2. always check branch and path before editing or committing

## Ownership Boundaries

### AI Assistant Workstream

Owns:

1. `experimental/qwen_agent_runtime/`
2. `impl_factory/03_config/qwen_enterprise_metadata/`
3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/`
4. assistant-specific governance, runtime, and hardening documents

### ERPNext UI Design Workstream

Owns:

1. `impl_factory/08_erpnext_ui_design/`
2. UI workspace design documents
3. navigation and layout design
4. UI planning, design decisions, and handoff notes
5. future UI-specific ERPNext frontend implementation areas when explicitly created

## Shared Surfaces Requiring Coordination

The following areas must not be changed casually by one stream without coordination:

1. app registration and installation surfaces
2. shared `hooks.py` or common app integration files
3. deployment or runtime config shared by both streams
4. repo-wide governance documents that change the execution plan for both streams
5. common build, test, or environment scripts used by both workstreams

Coordination rule:

1. if a change is required on a shared surface, record the reason in governance notes first
2. keep the change as small as possible
3. communicate ownership impact before merging to `main`

## Merge Policy

1. no direct feature development on `main`
2. feature branches merge into `main` only at intentional sync points
3. keep branch-specific commits scoped to the owned workstream
4. if a commit touches shared files, the commit message should make that explicit

## Practical Safety Rules

1. current AI Assistant work should leave `main` and continue on `feature/ai-assistant`
2. UI design work should start in a separate worktree on `feature/erpnext-ui-design`
3. do not place UI design raw references into assistant-owned folders
4. do not place assistant hardening or runtime experiments into the UI design folder
5. when uncertain, prefer creating a new governance note before changing shared repo structure

## Current Decision

The repository now treats parallel workstreams as a first-class operating model.

Completed setup:

1. move active AI Assistant development off `main`
2. create dedicated worktrees for `feature/ai-assistant` and `feature/erpnext-ui-design`
3. keep `main` reserved for controlled integration
4. publish `feature/ai-assistant` to `origin`

## Follow-Up

After the worktrees are created:

1. continue AI Assistant hardening only from the AI Assistant branch/worktree
2. begin UI design only from the UI design branch/worktree
3. revisit shared-surface rules before Wave 1 expansion or UI implementation integration
4. use the UI handoff note in `impl_factory/08_erpnext_ui_design/` when starting a fresh UI-design conversation
