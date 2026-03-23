# Qwen Legacy Runtime Purge Note

Date: 2026-03-23

## Scope

This cleanup removes the disconnected legacy OpenAI/manual agent stack and keeps only the code required for the governed Qwen assistant.

## Retained Core

1. `qwen_chat/*`
2. `experimental/qwen_agent_runtime/*`
3. governed metadata under `impl_factory/03_config/qwen_enterprise_metadata/*`
4. a minimal FAC bridge now located at:
   - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fac_client.py`

## Deleted Legacy Runtime

1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/`
2. old `AI Chat Session` doctype files
3. old `AI Chat Message` doctype files
4. old `ai-chat` page files
5. old automation packs under `impl_factory/04_automation/`
6. old governance docs tied to the removed manual/OpenAI path

## Config Cleanup

Legacy site-config keys were removed:

1. `ai_assistant_orchestrator_v2_enabled`
2. `ai_assistant_v3_canary_percent`
3. `ai_assistant_write_enabled`
4. `assistant_engine`
5. `openai_api_key`
6. `openai_model`

## Result

The repository now keeps the Qwen-governed assistant as the only active assistant runtime path, while preserving the minimal FAC integration needed for governed report execution.
