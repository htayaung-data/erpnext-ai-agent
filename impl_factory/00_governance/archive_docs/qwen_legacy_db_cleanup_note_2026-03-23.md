# Qwen Legacy DB Cleanup Note

Date: 2026-03-23

## Scope

Controlled database cleanup of legacy manual-agent artifacts that were no longer used by the Qwen-only stack:

- `AI Chat Session`
- `AI Chat Message`
- legacy `ai-chat` page metadata

## Dry-Run Inventory

Before deletion:

- `tabAI Chat Session`: 13 rows
- `tabAI Chat Message`: 431 rows
- `tabDocType` definitions: 2 rows
- `tabDocField` metadata: 4 rows
- `tabDocPerm` metadata: 1 row
- `tabPage` (`ai-chat`): 1 row
- `tabFile` attachments linked to `AI Chat Session`: 0 rows

## Cleanup Performed

Cleanup utility added at:

- `ai_assistant_ui/qwen_chat/maintenance.py`

Executed controlled cleanup in this order:

1. delete any legacy file attachments
2. delete legacy message rows
3. delete legacy session rows
4. delete legacy page metadata and page row
5. delete legacy doctype metadata rows
6. delete legacy doctype definitions
7. drop legacy database tables

## Result

After deletion:

- `tabAI Chat Session`: removed
- `tabAI Chat Message`: removed
- `tabDocType` legacy rows: removed
- `tabDocField` / `tabDocPerm` legacy metadata: removed
- `tabPage` (`ai-chat`): removed

## Verification

Post-cleanup verification completed:

- site cache cleared
- backend/frontend restarted
- Qwen clarification smoke passed
- Qwen natural narrative smoke passed

This leaves the repo and live site aligned on the Qwen-only governed assistant path.
