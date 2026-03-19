# Qwen Agent Runtime Prototype

This directory contains the external runtime for the `Qwen Chat` ERPNext prototype.

Enterprise target architecture is defined in:

- `impl_factory/00_governance/qwen_erp_enterprise_blueprint_2026-03-19.md`

## Purpose

- accept synchronous chat requests from the ERPNext app
- return deterministic mock responses first
- provide a clear upgrade path to `Qwen-Agent + Qwen/vLLM + FAC MCP`

## Endpoints

- `GET /health`
- `POST /chat`

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

`qwen-agent[mcp]` is included in `requirements.txt` for this prototype runtime.

For development with Alibaba Cloud Model Studio, use the OpenAI-compatible endpoint:

- `QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- `QWEN_MODEL=qwen3.5-plus`
- `QWEN_API_KEY=<your_dashscope_key>`
- `ENGINE_MODE=qwen_agent`

The runtime automatically disables thinking with the DashScope-compatible request shape when it detects a DashScope `compatible-mode` base URL.

For FAC MCP in this prototype, the recommended runtime settings are:

- `FAC_MCP_TRANSPORT=streamable-http`
- `FAC_AUTH_HEADER_NAME=Authorization`
- `FAC_AUTH_HEADER_VALUE=token <api_key>:<api_secret>`
- `FAC_ALLOWED_TOOLS` set to a read-only subset only

The current prototype intentionally blocks write-oriented FAC tools and uses a small tool budget to reduce agent looping.

If your MCP transport needs additional packages or settings, install them in the runtime environment and provide the matching env config.

## Recommended Initial Deployment

- ERPNext/Frappe stays on the current droplet
- this runtime can start on the same droplet in `mock` mode
- real `Qwen + vLLM` should run on a separate GPU host
- ERPNext calls this runtime server-to-server
