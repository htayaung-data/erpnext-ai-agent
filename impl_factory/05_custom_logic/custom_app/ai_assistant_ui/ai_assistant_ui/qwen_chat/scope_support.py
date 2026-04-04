from __future__ import annotations

import datetime as dt
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.contracts import normalize_scope_decision_input


def context_isolation_payload(*, request_id: str, decision: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"type": "qwen_context_isolation_decision",
		"request_id": str(request_id or "").strip(),
		"force_new_query": bool(decision.get("force_new_query")),
		"out_of_scope": bool(decision.get("out_of_scope")),
		"reason": str(decision.get("reason") or "").strip(),
		"requested_domains": list(decision.get("requested_domains") or []),
		"context_domains": list(decision.get("context_domains") or []),
		"primary_domain": str(decision.get("primary_domain") or "").strip(),
		"created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
	}


def out_of_scope_answer(message: str, decision: Dict[str, Any] | Any) -> str:
	normalized_decision = normalize_scope_decision_input(decision)
	primary_domain = str(normalized_decision.primary_domain or "").strip()
	if primary_domain == "finance":
		return (
			"I can help with governed financial statements, AR / AP, sales, inventory, product performance, invoices, and governed ERP drilldowns.\n\n"
			"This is a valid finance question, but this exact finance area is not yet covered as a governed Qwen ERP answer path."
		)
	if primary_domain == "hr":
		return (
			"I can help with finance, sales, inventory, product performance, invoices, and governed ERP drilldowns.\n\n"
			"I don't have governed HR or headcount coverage yet, so I can't answer staff-count questions confidently from ERP data in this assistant."
		)
	return (
		"I can help with finance, sales, inventory, product performance, invoices, and governed ERP drilldowns.\n\n"
		"This question falls outside the current governed Qwen ERP coverage, so I can't answer it confidently from ERP data yet."
	)
