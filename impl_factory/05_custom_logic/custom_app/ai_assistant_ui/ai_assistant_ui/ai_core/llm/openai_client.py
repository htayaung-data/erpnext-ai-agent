from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests
try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover - local test execution without Frappe runtime
    frappe = None


class OpenAIError(RuntimeError):
    pass


def _get_openai_cfg() -> tuple[str, str]:
    # site_config.json / common_site_config.json (Frappe conf)
    if frappe is None:
        raise OpenAIError("Frappe runtime is not available for OpenAI config lookup.")
    api_key = (frappe.conf.get("openai_api_key") or "").strip()
    model = (frappe.conf.get("openai_model") or "gpt-4o-mini").strip()
    if not api_key:
        raise OpenAIError("OpenAI API key is not configured in site config.")
    return api_key, model


def chat_completions_json(
    *,
    system: str,
    user: str,
    temperature: float = 0.0,
    max_tokens: int = 900,
    timeout: int = 45,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    api_key, default_model = _get_openai_cfg()
    use_model = model or default_model

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": use_model,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
        data = resp.json()
    except Exception as e:
        raise OpenAIError(f"OpenAI request failed: {e}") from e

    if resp.status_code >= 400:
        raise OpenAIError(f"OpenAI error {resp.status_code}: {str(data)[:500]}")

    try:
        content = data["choices"][0]["message"]["content"]
        obj = json.loads(content)
        if not isinstance(obj, dict):
            raise OpenAIError("Planner returned non-object JSON.")
        return obj
    except Exception as e:
        raise OpenAIError(f"Planner response parse failed: {e}. Raw: {str(data)[:500]}") from e
