# Qwen Agent Runtime

This directory contains the external runtime for the `Qwen Chat` ERPNext path.

Enterprise target architecture is defined in:

- `impl_factory/00_governance/qwen_erp_enterprise_blueprint_2026-03-19.md`

## Purpose

- accept synchronous chat requests from the ERPNext app
- support governed `Qwen-Agent + FAC MCP` execution
- provide a clear upgrade path to self-hosted `Qwen/vLLM`

## Endpoints

- `GET /health`
- `POST /chat`
- `POST /interpret-fresh-query`
- `POST /interpret-followup`

## Modes

- `ENGINE_MODE=mock`
  - deterministic responses
  - no model or MCP dependency
- `ENGINE_MODE=qwen_agent`
  - uses `Qwen-Agent` if installed and configured
  - expects Qwen to be available through an OpenAI-compatible endpoint such as `vLLM`

## Quick Start (Mock Mode)

```bash
cd /home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8010
```

If you prefer Docker on this droplet:

```bash
cd /home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime
cp .env.example .env
docker compose up -d --build
```

Then configure the ERP app with:

- `qwen_agent_runtime_base_url = "http://<runtime-host>:8010"`
- `qwen_agent_runtime_timeout = 30`
- optional `qwen_agent_runtime_api_token`

If ERPNext is calling this runtime from inside Docker, do not use `http://localhost:8010` unless the runtime is in the same container. Use a routable host or domain that the ERP backend container can reach.

## Qwen-Agent Mode Notes

`qwen-agent[mcp]` is included in `requirements.txt` for this runtime.

For development with Alibaba Cloud Model Studio, use the OpenAI-compatible endpoint:

- `QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- `QWEN_MODEL=qwen-plus`
- `QWEN_API_KEY=<your_dashscope_key>`
- `ENGINE_MODE=qwen_agent`

The runtime automatically disables thinking with the DashScope-compatible request shape when it detects a DashScope `compatible-mode` base URL.

For FAC MCP in this runtime, the recommended settings are:

- `FAC_MCP_TRANSPORT=streamable-http`
- `FAC_AUTH_HEADER_NAME=Authorization`
- `FAC_AUTH_HEADER_VALUE=token <api_key>:<api_secret>`
- `FAC_ALLOWED_TOOLS` set to a read-only subset only

The current runtime intentionally blocks write-oriented FAC tools and uses a bounded tool budget to reduce agent looping.

Additional follow-up interpretation controls:

- `SEMANTIC_FRESH_QUERY_TIMEOUT_SECONDS=90`
- `SEMANTIC_FRESH_QUERY_MAX_ATTEMPTS=2`
- `SEMANTIC_FRESH_QUERY_BACKOFF_MS=350`
- `SEMANTIC_FRESH_QUERY_MODEL=...` optional model override for first-turn proposal generation
- `SEMANTIC_FRESH_QUERY_MAX_TOKENS=320`
- `SEMANTIC_FRESH_QUERY_CACHE_TTL_SECONDS=300`
- `SEMANTIC_FRESH_QUERY_CACHE_MAX_ENTRIES=256`
- `SEMANTIC_FOLLOWUP_MODEL=...` optional model override for governed follow-up interpretation
- `SEMANTIC_FOLLOWUP_MAX_ATTEMPTS=2`
- `SEMANTIC_FOLLOWUP_BACKOFF_MS=350`

These control retry/backoff behavior for the semantic fresh-query and semantic follow-up interpreters.
The fresh-query cache is an in-memory runtime cache for repeated governed proposal requests with the same message and interpretation context. It does not bypass compiler enforcement.
If cold-path proposal latency remains too high, prefer setting `SEMANTIC_FRESH_QUERY_MODEL` and `SEMANTIC_FOLLOWUP_MODEL` to a faster Qwen model for semantic interpretation before changing the governed compiler boundary.

## Development Split

The current recommended development split on the hosted Qwen API is:

- `QWEN_MODEL=qwen-plus` for grounded runtime/tool use
- `SEMANTIC_FRESH_QUERY_MODEL=qwen-turbo` for first-turn proposal generation
- `SEMANTIC_FOLLOWUP_MODEL=qwen-turbo` for governed follow-up interpretation

This keeps the governed compiler boundary intact while reducing latency on semantic classification and slot extraction.

## Single-Model Default

The recommended production default is still:

- one hosted Qwen model for both proposal generation and grounded runtime/tool use

That means:

- set `QWEN_MODEL` normally
- leave `SEMANTIC_FRESH_QUERY_MODEL` empty

In that posture:

- the fresh-query proposal step and the grounded runtime both use the same hosted model
- the architecture still keeps proposal and runtime logically separate
- a second proposal model is only an optional later latency optimization

If the ERP site is using the fresh-query advisory compiler path, it may also set:

- `qwen_agent_runtime_fresh_query_timeout`

This timeout is intentionally allowed to be higher than the normal chat timeout because first-turn semantic proposal generation can be slower than grounded follow-up interpretation.

If your MCP transport needs additional packages or settings, install them in the runtime environment and provide the matching env config.

## Recommended Initial Deployment

- ERPNext/Frappe stays on the current droplet
- this runtime can start on the same droplet in `mock` mode
- real `Qwen + vLLM` should run on a separate GPU host
- ERPNext calls this runtime server-to-server
