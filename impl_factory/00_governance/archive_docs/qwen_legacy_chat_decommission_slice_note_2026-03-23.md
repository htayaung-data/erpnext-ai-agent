# Qwen Legacy Chat Decommission Slice

Date: 2026-03-23

## Scope

This slice retired the old OpenAI/manual `ai-chat` user-facing surface as an intermediate step before the full legacy runtime purge.

## What Changed

1. `api.chat_send` and legacy session endpoints no longer invoked the old manual runtime.
2. The old runtime import was removed from the public API surface, so new user traffic could not enter the legacy OpenAI/manual chat path.

## Superseded

This note is now superseded by the full purge recorded in:

- `impl_factory/00_governance/qwen_legacy_runtime_purge_note_2026-03-23.md`
