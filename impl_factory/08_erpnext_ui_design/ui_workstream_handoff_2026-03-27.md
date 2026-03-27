# ERPNext UI Workstream Charter And Handoff (2026-03-27)

## Purpose

This note is the operating charter for the ERPNext UI design workstream.

It exists to make three things explicit:

1. where UI work should happen
2. what this workstream owns
3. what must stay coordinated with the AI Assistant workstream

Use this note when starting a new UI-focused conversation or when re-entering the UI branch after working elsewhere.

## Current Repository Setup

The repository is intentionally split into separate worktrees so AI Assistant engineering and ERPNext UI design can move in parallel without accidental file mixing.

Current worktrees:

1. AI Assistant engineering
   - branch: `feature/ai-assistant`
   - path: `/home/deploy/erp-projects/erpai_project1`
2. ERPNext UI design
   - branch: `feature/erpnext-ui-design`
   - path: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
3. clean integration
   - branch: `main`
   - path: `/home/deploy/erp-projects/erpai_project1_main_integration`

Operational meaning:

1. `main` is integration-only
2. active UI work happens only in the UI worktree
3. active AI Assistant work happens only in the AI worktree

## What Has Already Been Completed

The parallel setup is already established:

1. active AI Assistant development was moved off `main`
2. `feature/ai-assistant` became the active assistant branch
3. `feature/erpnext-ui-design` was created for UI work
4. the UI worktree was created at `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
5. the clean integration worktree was created for `main`
6. `impl_factory/08_erpnext_ui_design/` was initialized as the managed home for this workstream

## UI Workstream Scope

This workstream owns:

1. `impl_factory/08_erpnext_ui_design/`
2. raw UI reference material
3. working design notes
4. navigation, layout, and workspace planning
5. design decisions and handoff notes
6. future UI-specific ERPNext frontend implementation areas when explicitly created

Practical rule:

1. UI-only design and governance notes should stay inside `impl_factory/08_erpnext_ui_design/`
2. cross-workstream governance belongs only in shared repository governance when it affects both streams

## Non-Owned Areas

This UI workstream should not edit the active assistant surfaces during the design phase:

1. `experimental/qwen_agent_runtime/`
2. `impl_factory/03_config/qwen_enterprise_metadata/`
3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/`

Also avoid:

1. moving UI notes into assistant-owned folders
2. doing feature work directly on `main`
3. treating shared repo governance as the default location for UI-only planning

## Shared Surfaces Requiring Coordination

The following areas require coordination before editing:

1. app registration and installation surfaces
2. shared `hooks.py` or common integration files
3. deployment or runtime configuration used by both streams
4. repo-wide governance documents that change operating rules for both streams
5. common scripts for build, test, environment, or setup

Coordination rule:

1. if a shared surface must change, record the reason first
2. keep the change minimal and explicit
3. make ownership impact clear before merge to `main`

## Working Rules For New UI Conversations

When a fresh UI-design conversation starts, it should:

1. work only inside `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
2. confirm the branch is `feature/erpnext-ui-design`
3. keep new UI docs under `impl_factory/08_erpnext_ui_design/`
4. place early exploration, assumptions, and design decisions here before proposing shared-file edits
5. avoid depending on assistant runtime changes during the design phase

Useful reminder:

1. untracked files under `impl_factory/08_erpnext_ui_design/` are expected while this design stream is being built out
2. that is normal as long as the work stays inside the UI-owned folder

## Recommended Document Structure

As the UI stream grows, keep this folder organized with small, purpose-based sections such as:

1. `references/`
2. `discovery/`
3. `navigation/`
4. `layout/`
5. `design-decisions/`
6. `handoff/`

This structure is guidance, not a hard constraint. Use it when it improves clarity.

## Context About The AI Assistant Workstream

The AI Assistant workstream is in active post-contract hardening.

That means:

1. assistant runtime files may change frequently
2. assistant governance and hardening notes remain active
3. UI work should not assume assistant-owned files are stable editing targets

## Practical Safety Check

Before starting UI work, verify:

1. current path is `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
2. current branch is `feature/erpnext-ui-design`

That simple check prevents most cross-workstream mistakes.
                                    