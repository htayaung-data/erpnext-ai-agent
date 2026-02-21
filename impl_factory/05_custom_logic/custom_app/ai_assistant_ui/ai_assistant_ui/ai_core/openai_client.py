import json
import requests
import frappe


class OpenAIClient:
    """
    Minimal OpenAI ChatCompletions client with tool-calling support.
    Reads config at runtime (no import-time crashes).
    """

    def __init__(self):
        self.api_key = (frappe.conf.get("openai_api_key") or "").strip()
        self.model = (frappe.conf.get("openai_model") or "gpt-4o-mini").strip()
        self.base_url = (frappe.conf.get("openai_base_url") or "https://api.openai.com/v1").rstrip("/")

        if not self.api_key:
            raise RuntimeError("OpenAI API key is not configured (openai_api_key).")

    def chat_completions(self, messages, tools=None, tool_choice="auto", temperature=0.2, timeout=90):
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": messages, "temperature": float(temperature)}

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
        if resp.status_code >= 400:
            try:
                j = resp.json()
            except Exception:
                j = {"error": {"message": resp.text[:500]}}
            raise RuntimeError(f"OpenAI error ({resp.status_code}): {j.get('error', {}).get('message', 'Unknown error')}")
        return resp.json()
