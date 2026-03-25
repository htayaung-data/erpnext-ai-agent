from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.metadata import (
	all_ontology_concepts,
	ontology_detect_concepts,
	supported_ontology_concepts,
)


@dataclass(frozen=True)
class ScopeDecisionInputContract:
	force_new_query: bool = False
	out_of_scope: bool = False
	reason: str = ""
	requested_domains: List[str] | None = None
	context_domains: List[str] | None = None
	primary_domain: str = ""

	def to_payload(self) -> Dict[str, Any]:
		return {
			"force_new_query": bool(self.force_new_query),
			"out_of_scope": bool(self.out_of_scope),
			"reason": str(self.reason or "").strip(),
			"requested_domains": [
				str(value or "").strip()
				for value in (self.requested_domains or [])
				if str(value or "").strip()
			],
			"context_domains": [
				str(value or "").strip()
				for value in (self.context_domains or [])
				if str(value or "").strip()
			],
			"primary_domain": str(self.primary_domain or "").strip(),
		}


def build_scope_decision_input(
	*,
	force_new_query: bool = False,
	out_of_scope: bool = False,
	reason: str = "",
	requested_domains: List[str] | None = None,
	context_domains: List[str] | None = None,
	primary_domain: str = "",
) -> ScopeDecisionInputContract:
	return ScopeDecisionInputContract(
		force_new_query=bool(force_new_query),
		out_of_scope=bool(out_of_scope),
		reason=str(reason or "").strip(),
		requested_domains=[
			str(value or "").strip()
			for value in (requested_domains or [])
			if str(value or "").strip()
		],
		context_domains=[
			str(value or "").strip()
			for value in (context_domains or [])
			if str(value or "").strip()
		],
		primary_domain=str(primary_domain or "").strip(),
	)


def normalize_scope_decision_input(
	value: ScopeDecisionInputContract | Dict[str, Any] | None = None,
) -> ScopeDecisionInputContract:
	if isinstance(value, ScopeDecisionInputContract):
		return build_scope_decision_input(
			force_new_query=bool(value.force_new_query),
			out_of_scope=bool(value.out_of_scope),
			reason=str(value.reason or "").strip(),
			requested_domains=list(value.requested_domains or []),
			context_domains=list(value.context_domains or []),
			primary_domain=str(value.primary_domain or "").strip(),
		)
	source = value if isinstance(value, dict) else {}
	return build_scope_decision_input(
		force_new_query=bool(source.get("force_new_query")),
		out_of_scope=bool(source.get("out_of_scope")),
		reason=str(source.get("reason") or "").strip(),
		requested_domains=list(source.get("requested_domains") or []),
		context_domains=list(source.get("context_domains") or []),
		primary_domain=str(source.get("primary_domain") or "").strip(),
	)


def build_known_unsupported_scope_decision_input(
	*,
	raw_message: str,
	context_domains: List[str] | None = None,
) -> ScopeDecisionInputContract | None:
	message_concepts = {
		str(value or "").strip()
		for value in ontology_detect_concepts(raw_message)
		if str(value or "").strip()
	}
	if not message_concepts:
		return None
	supported = set(supported_ontology_concepts())
	known = set(all_ontology_concepts())
	unsupported_known = sorted(concept for concept in message_concepts if concept in known and concept not in supported)
	if not unsupported_known:
		return None
	primary_domain = ""
	if {"tax", "balance_sheet", "cash_flow", "profit_and_loss", "working_capital", "payable", "receivable"} & set(unsupported_known):
		primary_domain = "finance"
	elif "employee" in unsupported_known:
		primary_domain = "hr"
	return build_scope_decision_input(
		force_new_query=True,
		out_of_scope=True,
		reason="The request targets a valid ERP business area that is not yet covered by the current governed assistant.",
		requested_domains=unsupported_known,
		context_domains=context_domains,
		primary_domain=primary_domain,
	)
