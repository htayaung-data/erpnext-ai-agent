from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Dict, Iterable, List


CONTRACT_VERSION = "1.0"
USER_INTENT_BOUNDARY_CONTRACT_TYPE = "qwen_user_intent_boundary_contract"
USER_INTENT_BOUNDARY_SOURCE = "deterministic_user_intent_safety_boundary"

CATEGORY_FACTUAL_ERP_QUERY = "factual_erp_query"
CATEGORY_CLARIFICATION_REQUIRED = "clarification_required"
CATEGORY_TRUE_FOLLOWUP = "true_followup"
CATEGORY_AMBIGUOUS_FOLLOWUP = "ambiguous_followup"
CATEGORY_PREDICTION_OR_FORECAST = "prediction_or_forecast"
CATEGORY_RECOMMENDATION_OR_BUSINESS_ADVICE = "recommendation_or_business_advice"
CATEGORY_LEGAL_OR_REGULATORY_ADVICE = "legal_or_regulatory_advice"
CATEGORY_WRITE_OR_MUTATION_ACTION = "write_or_mutation_action"
CATEGORY_FRAUD_OR_MANIPULATION = "fraud_or_manipulation"
CATEGORY_UNSUPPORTED_DECISION_REQUEST = "unsupported_decision_request"

ALLOWED_USER_INTENT_BOUNDARY_CATEGORIES = {
	CATEGORY_FACTUAL_ERP_QUERY,
	CATEGORY_CLARIFICATION_REQUIRED,
	CATEGORY_TRUE_FOLLOWUP,
	CATEGORY_AMBIGUOUS_FOLLOWUP,
	CATEGORY_PREDICTION_OR_FORECAST,
	CATEGORY_RECOMMENDATION_OR_BUSINESS_ADVICE,
	CATEGORY_LEGAL_OR_REGULATORY_ADVICE,
	CATEGORY_WRITE_OR_MUTATION_ACTION,
	CATEGORY_FRAUD_OR_MANIPULATION,
	CATEGORY_UNSUPPORTED_DECISION_REQUEST,
}

ANSWER_MODE_GOVERNED_ERP = "governed_erp_answer"
ANSWER_MODE_CLARIFICATION = "clarification"
ANSWER_MODE_POLICY_BOUNDARY = "policy_boundary"
ANSWER_MODE_CONTROL_BOUNDARY = "control_boundary"

ALLOWED_USER_INTENT_BOUNDARY_ANSWER_MODES = {
	ANSWER_MODE_GOVERNED_ERP,
	ANSWER_MODE_CLARIFICATION,
	ANSWER_MODE_POLICY_BOUNDARY,
	ANSWER_MODE_CONTROL_BOUNDARY,
}

DOMAIN_CUSTOMER_SUPPLIER_ADMISSION_RETENTION = "customer_supplier_admission_retention"
DOMAIN_PRODUCT_CATALOG_LIFECYCLE = "product_catalog_lifecycle"
DOMAIN_PROCUREMENT_ORDERING_RESTOCKING = "procurement_ordering_restocking"
DOMAIN_INVENTORY_LEVEL_DISPOSAL_OBSOLESCENCE = "inventory_level_disposal_obsolescence"
DOMAIN_ACCOUNTING_VALUATION_OBSOLESCENCE_LIFECYCLE = "accounting_valuation_obsolescence_lifecycle"
DOMAIN_PRICING_DISCOUNT_VALUATION_DECISION = "pricing_discount_valuation_decision"
DOMAIN_PAYMENT_DELAY_WITHHOLDING = "payment_delay_withholding"
DOMAIN_REPORT_HIDING_MANIPULATION = "report_hiding_manipulation"
DOMAIN_ACCOUNTING_WRITEOFF_ADJUSTMENT = "accounting_writeoff_adjustment"
DOMAIN_LEGAL_REGULATORY = "legal_regulatory"
DOMAIN_WRITE_MUTATION_ACTION = "write_mutation_action"
DOMAIN_NONE = "none"

_ERP_ID_RE = re.compile(r"\bec7h-(cust|sup|item|sinv)-[a-z0-9-]+\b")
_THIS_THAT_ENTITY_RE = re.compile(
	r"\b(this|that)\s+(customer|supplier|vendor|product|item|invoice|row|report|payment|record)\b"
)
_ENTITY_NOUNS = {
	"customer",
	"customers",
	"supplier",
	"suppliers",
	"vendor",
	"vendors",
	"product",
	"products",
	"item",
	"items",
	"invoice",
	"invoices",
	"row",
	"rows",
	"report",
	"reports",
	"payment",
	"payments",
	"journal entry",
	"inventory",
	"stock",
	"catalog",
	"list",
	"order",
	"orders",
}

_SAFE_FACTUAL_LOOKUP_VERBS = (
	"show",
	"display",
	"list",
	"get",
	"give",
	"provide",
	"compare",
	"open",
	"what is",
	"what",
	"who is",
	"who",
	"which",
	"top",
	"how much",
	"how",
	"are",
	"is",
)
_SAFE_FACTUAL_LOOKUP_OBJECTS = (
	"payable status",
	"supplier payment status",
	"supplier payable aging",
	"supplier aging",
	"outstanding balance",
	"customer outstanding",
	"customer details",
	"supplier details",
	"item details",
	"item price",
	"item sales",
	"product sales",
	"customer sales",
	"invoice details",
	"invoice due date",
	"overdue invoices",
	"unpaid invoices",
	"payment status",
	"aging",
	"sales",
	"balance",
	"price",
	"details",
	"status",
	"profit",
	"profitable",
	"p&l",
	"pnl",
	"accounts receivable",
	"accounts payable",
	"ar",
	"ap",
	"owes us",
	"owe suppliers",
	"owes",
	"owe",
	"bought",
	"sales qty",
	"top items",
	"money",
)

_READ_ONLY_FOLLOWUP_INTENTS = (
	"show details",
	"show detail",
	"display details",
	"open",
	"explain",
	"who is",
	"what is in",
	"number",
	"rank",
	"previous table",
	"same table",
	"above list",
	"above context",
	"first invoice",
	"second",
	"third",
	"fourth",
	"fifth",
)
_TRUE_FOLLOWUP_CONTEXT_REFERENCES = (
	"that",
	"this",
	"number",
	"rank",
	"previous",
	"same",
	"above",
	"first",
	"second",
	"third",
	"fourth",
	"fifth",
)

_DECISION_MODE_PHRASES = (
	"should",
	"can",
	"could",
	"would",
	"may",
	"do we",
	"do i",
	"is it okay",
	"is it ok",
	"is it allowed",
	"is it acceptable",
	"is it worth",
	"worth",
	"whether",
	"if",
	"why",
	"good idea",
	"makes sense",
	"allowed",
	"best",
	"right",
	"wrong",
	"recommend",
	"recommendation",
	"advise",
	"what would you do",
	"what should we do",
	"what should i do",
)

_PREDICTION_SIGNALS = (
	"predict",
	"forecast",
	"project",
	"likely",
	"probably",
	"will",
	"next month",
	"next quarter",
	"next year",
	"future",
	"default",
)

_LEGAL_SIGNALS = (
	"legal",
	"legally",
	"law",
	"lawyer",
	"attorney",
	"court",
	"sue",
	"sued",
	"lawsuit",
	"lawsuit",
	"regulatory",
	"regulation",
	"compliance",
)

_REPORT_HIDING_SIGNALS = (
	"hide",
	"conceal",
	"suppress",
	"omit",
	"leave out",
	"not show",
	"do not show",
	"not display",
	"not include",
	"do not include",
	"avoid mentioning",
	"not mention",
	"exclude",
	"excluding",
	"remove bad",
	"remove overdue",
	"remove problem",
	"ignore",
	"ignoring",
	"skip",
	"skipping",
	"clean up",
	"make profit look better",
	"make profits look better",
	"make sales look better",
	"make revenue look better",
	"make profit nicer",
	"make the profit nicer",
	"massage",
	"smooth",
	"falsify",
	"manipulate",
	"misstate",
	"fake",
	"doctor",
)
_REPORT_HIDING_TARGETS = (
	"invoice",
	"invoices",
	"row",
	"rows",
	"report",
	"reports",
	"bad",
	"late",
	"overdue",
	"problem",
	"profit",
	"profits",
	"sales",
	"revenue",
	"numbers",
)

_PAYMENT_DELAY_SIGNALS = (
	"delay",
	"delayed",
	"delaying",
	"defer",
	"deferred",
	"postpone",
	"put off",
	"wait",
	"hold",
	"pause",
	"skip",
	"not pay",
	"no need pay",
	"need not pay",
	"leave unpaid",
	"stay unpaid",
	"remain unpaid",
	"pay late",
	"pay later",
	"settle later",
	"withhold",
	"push",
)
_PAYMENT_TEMPORAL_SIGNALS = (
	"later",
	"late",
	"next week",
	"next month",
	"tomorrow",
	"until",
	"after",
	"instead",
	"for a while",
)

_CUSTOMER_SUPPLIER_RETENTION_SIGNALS = (
	"keep",
	"keeping",
	"kept",
	"retain",
	"retaining",
	"retained",
	"continue",
	"continuing",
	"continued",
	"remove",
	"removing",
	"removed",
	"drop",
	"dropped",
	"stop",
	"stopped",
	"deactivate",
	"deactivated",
	"activate",
	"activated",
	"stay active",
	"remain active",
	"stay as",
	"remain supplier",
	"remain customer",
	"remain a supplier",
	"remain a customer",
	"continue as",
	"keep as",
	"be our supplier",
	"be our customer",
	"be added",
	"add",
	"approve",
	"approved",
	"customer list",
	"supplier list",
	"vendor list",
)

_PRODUCT_CATALOG_LIFECYCLE_SIGNALS = (
	"keep",
	"keeping",
	"kept",
	"retain",
	"retaining",
	"retained",
	"continue",
	"continuing",
	"continued",
	"remove",
	"removing",
	"removed",
	"drop",
	"dropped",
	"stop",
	"stopped",
	"discontinue",
	"discontinued",
	"discontinuing",
	"deactivate",
	"deactivated",
	"activate",
	"activated",
	"stay active",
	"remain active",
	"stay available",
	"remain available",
	"available for sale",
	"continue selling",
	"keep selling",
	"stop selling",
	"sell",
	"sold",
	"use",
	"list",
	"listed",
	"listed",
	"catalog",
	"catalog item",
	"become",
	"be our product",
	"be our item",
	"approve",
	"approved",
	"add",
	"added",
)

_PROCUREMENT_ORDERING_SIGNALS = (
	"buy",
	"purchase",
	"procure",
	"order",
	"reorder",
	"ordered",
	"reordered",
	"restock",
	"restocked",
	"restocking",
	"replenish",
	"replenished",
	"replenishing",
	"source",
	"carry",
	"stock",
	"stocked",
	"stocking",
	"bring in",
)

_INVENTORY_DISPOSAL_SIGNALS = (
	"increase inventory",
	"decrease inventory",
	"build inventory",
	"build up inventory",
	"cut inventory",
	"trim inventory",
	"shrink inventory",
	"expand inventory",
	"raise stock",
	"lower stock",
	"increase orders",
	"reduce orders",
	"run down",
	"draw down",
	"wind down",
	"run off",
	"phase out",
	"phased out",
	"clear out",
	"get rid of",
	"dispose of",
	"liquidate",
	"write off",
	"written off",
	"write down",
	"written down",
	"scrap",
	"scrapped",
	"retire",
	"retired",
	"mark obsolete",
	"marked obsolete",
	"obsolete",
	"stay in inventory",
	"remain in inventory",
	"stay on hand",
	"remain on hand",
)

_ACCOUNTING_VALUATION_OBSOLESCENCE_SIGNALS = (
	"mark down",
	"marked down",
	"impair",
	"impaired",
	"devalue",
	"devalued",
	"obsolete",
	"obsoleted",
	"scrap",
	"scrapped",
	"retire",
	"retired",
	"write down",
	"written down",
)
_ACCOUNTING_VALUATION_CONTEXT = (
	"book value",
	"carrying value",
	"valuation",
	"impairment",
	"write down",
	"mark down",
	"obsolete",
	"obsolescence",
)

_PRICING_DISCOUNT_VALUATION_SIGNALS = (
	"discount",
	"discounted",
	"lower price",
	"lower its price",
	"reduce price",
	"reduce its price",
	"mark down",
	"marked down",
	"markdown",
	"overpriced",
	"price too high",
	"too expensive",
)
_PRICING_DISCOUNT_VALUATION_CONTEXT = (
	"price",
	"pricing",
	"discount",
	"markdown",
	"mark down",
	"overpriced",
)

_ACCOUNTING_ACTION_SIGNALS = (
	"journal entry",
	"adjust",
	"reverse",
	"revise",
	"change",
	"update",
	"edit",
	"amend",
	"modify",
	"back date",
	"backdate",
	"write off",
	"write-off",
	"approve",
	"post",
	"submit",
	"cancel",
	"delete",
	"void",
	"mark paid",
	"set paid",
)
_MUTATION_TARGETS = (
	"invoice",
	"journal entry",
	"payment",
	"supplier",
	"customer",
	"sales order",
	"purchase order",
	"due date",
	"record",
	"balance",
	"receivable",
	"debt",
)
_MUTATION_ACTION_TERMS = (
	"change",
	"changed",
	"update",
	"updated",
	"edit",
	"amend",
	"modify",
	"revise",
	"adjust",
	"adjusted",
	"reverse",
	"reversed",
	"deactivate",
	"deactivated",
	"activate",
	"activated",
	"mark",
	"marked",
	"set",
	"approve",
	"approved",
	"post",
	"submit",
	"cancel",
	"delete",
	"void",
	"backdate",
	"back date",
	"remove",
	"removing",
	"removed",
)

_CLARIFICATION_PATTERNS = (
	r"^\s*(money\s+coming\s+in|how\s+is\s+business|is\s+everything\s+okay)\??\s*$",
	r"\binvoice\s+detail\s*(pls|please)?\b",
	r"\bfind\s+invoice\s+by\s+customer\s+name\b",
	r"\binv\s+\d+\s+(amt|amount)\b",
	r"\bbest\s+customer\s+today\b",
	r"\bap\s+due\s+soon\b",
	r"\bsales\s+bad\b",
	r"\bwhich\s+invoices\b.*\bunpaid\b.*\blargest\s+customer\b",
)
_AMBIGUOUS_FOLLOWUP_PATTERNS = (
	r"^\s*(ok\s+next|next|continue|go on|and then|same\??|what about it|more)\s*$",
)


@dataclass(frozen=True)
class UserIntentBoundaryDecision:
	category: str
	context_reuse_allowed: bool
	report_routing_allowed: bool
	required_answer_mode: str
	boundary_reason: str
	original_user_text_hash: str = ""
	source: str = USER_INTENT_BOUNDARY_SOURCE
	contract_version: str = CONTRACT_VERSION

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
			"contract_version": self.contract_version,
			"category": self.category,
			"context_reuse_allowed": bool(self.context_reuse_allowed),
			"report_routing_allowed": bool(self.report_routing_allowed),
			"required_answer_mode": self.required_answer_mode,
			"boundary_reason": self.boundary_reason,
			"source": self.source,
			"original_user_text_hash": self.original_user_text_hash,
		}


def allowed_user_intent_boundary_values() -> Dict[str, List[str]]:
	return {
		"categories": sorted(ALLOWED_USER_INTENT_BOUNDARY_CATEGORIES),
		"answer_modes": sorted(ALLOWED_USER_INTENT_BOUNDARY_ANSWER_MODES),
	}


def normalize_user_text(raw_message: Any) -> str:
	text = str(raw_message or "").strip().lower()
	text = re.sub(r"[\u2018\u2019]", "'", text)
	text = re.sub(r"[\u201c\u201d]", '"', text)
	text = text.replace("write-off", "write off")
	text = text.replace("write-down", "write down")
	text = text.replace("back-date", "back date")
	text = re.sub(r"[?!,.;:()\[\]{}]+", " ", text)
	text = re.sub(r"\s+", " ", text)
	return text.strip()


def _normalize_text(value: Any) -> str:
	return normalize_user_text(value)


def _message_hash(value: Any) -> str:
	text = str(value or "").strip()
	if not text:
		return ""
	return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _phrase_pattern(phrase: str) -> str:
	escaped = re.escape(phrase).replace(r"\ ", r"\s+")
	return rf"(?<![a-z0-9-]){escaped}(?![a-z0-9-])"


def _contains_phrase(text: str, phrase: str) -> bool:
	return re.search(_phrase_pattern(phrase), text) is not None


def _contains_any_phrase(text: str, phrases: Iterable[str]) -> bool:
	return any(_contains_phrase(text, phrase) for phrase in phrases)


def _phrase_position_after(text: str, phrase: str, start: int) -> int | None:
	for match in re.finditer(_phrase_pattern(phrase), text):
		if match.start() > start:
			return match.start()
	return None


def _contains_ordered_phrase_groups(text: str, phrase_groups: Iterable[Iterable[str]]) -> bool:
	cursor = -1
	for phrases in phrase_groups:
		next_positions = [
			position
			for phrase in phrases
			for position in [_phrase_position_after(text, phrase, cursor)]
			if position is not None
		]
		if not next_positions:
			return False
		cursor = min(next_positions)
	return True


def _matches_any(patterns: tuple[str, ...], text: str) -> bool:
	return any(re.search(pattern, text) for pattern in patterns)


def extract_erp_targets(text: str) -> Dict[str, Any]:
	erp_ids = [match.group(0) for match in _ERP_ID_RE.finditer(text)]
	id_families = {match.group(1) for match in _ERP_ID_RE.finditer(text)}
	deictic_entities = [match.group(0) for match in _THIS_THAT_ENTITY_RE.finditer(text)]
	entity_nouns = sorted(noun for noun in _ENTITY_NOUNS if _contains_phrase(text, noun))
	return {
		"erp_ids": erp_ids,
		"id_families": sorted(id_families),
		"deictic_entities": deictic_entities,
		"entity_nouns": entity_nouns,
		"has_target": bool(erp_ids or deictic_entities or entity_nouns),
	}


def _has_target_family(targets: Dict[str, Any], families: set[str]) -> bool:
	if set(targets["id_families"]) & families:
		return True
	entity_nouns = set(targets["entity_nouns"])
	if families & {"cust"} and entity_nouns & {"customer", "customers"}:
		return True
	if families & {"sup"} and entity_nouns & {"supplier", "suppliers", "vendor", "vendors"}:
		return True
	if families & {"item"} and entity_nouns & {"product", "products", "item", "items", "catalog", "inventory", "stock"}:
		return True
	if families & {"sinv"} and entity_nouns & {"invoice", "invoices"}:
		return True
	return False


def detect_safe_factual_lookup(text: str) -> bool:
	has_read_verb = _contains_any_phrase(text, _SAFE_FACTUAL_LOOKUP_VERBS)
	has_lookup_object = _contains_any_phrase(text, _SAFE_FACTUAL_LOOKUP_OBJECTS)
	has_explicit_erp_lookup = bool(_ERP_ID_RE.search(text)) and has_read_verb and has_lookup_object
	has_report_shape = has_read_verb and has_lookup_object
	return bool(has_report_shape or has_explicit_erp_lookup)


def detect_decision_question_mode(text: str) -> bool:
	return _contains_any_phrase(text, _DECISION_MODE_PHRASES)


def _looks_like_prediction(text: str) -> bool:
	if not _contains_any_phrase(text, ("predict", "forecast", "project", "likely", "probably", "will", "default", "future")):
		return False
	return _contains_any_phrase(text, ("profit", "cash", "default", "pay", "sales", "revenue", "customer", "supplier"))


def _looks_like_unsupported_decision(text: str) -> bool:
	return _contains_any_phrase(
		text,
		(
			"what should we do",
			"what should i do",
			"what would you do",
			"which one should i choose",
			"make the decision",
			"what should i look at first",
		),
	)


def _looks_like_payment_delay_domain(text: str, targets: Dict[str, Any]) -> bool:
	has_supplier_context = _has_target_family(targets, {"sup"}) or _contains_phrase(text, "supplier payment")
	if not has_supplier_context:
		return False
	if _contains_any_phrase(text, _PAYMENT_DELAY_SIGNALS):
		return True
	has_pay_reference = _contains_any_phrase(text, ("pay", "paying", "payment", "unpaid"))
	return has_pay_reference and _contains_any_phrase(text, _PAYMENT_TEMPORAL_SIGNALS)


def _looks_like_report_hiding_domain(text: str, targets: Dict[str, Any]) -> bool:
	has_report_context = _has_target_family(targets, {"sinv"}) or _contains_any_phrase(
		text,
		_REPORT_HIDING_TARGETS,
	)
	if not has_report_context:
		return False
	if _contains_ordered_phrase_groups(
		text,
		(
			("remove",),
			("bad", "overdue", "problem", "late"),
			("invoice", "invoices", "row", "rows", "report", "reports"),
		),
	):
		return True
	if _contains_ordered_phrase_groups(
		text,
		(("make",), ("look",), ("better", "nicer"), _REPORT_HIDING_TARGETS),
	):
		return True
	if _contains_ordered_phrase_groups(
		text,
		(("make",), _REPORT_HIDING_TARGETS, ("look better", "look nicer", "better", "nicer")),
	):
		return True
	if _contains_any_phrase(text, _REPORT_HIDING_SIGNALS):
		return True
	return _contains_ordered_phrase_groups(text, (("leave",), ("out",))) or _contains_any_phrase(
		text,
		("skipped", "ignored", "excluded", "removed", "hidden", "omitted"),
	)


def _looks_like_write_mutation_domain(text: str, targets: Dict[str, Any]) -> bool:
	if (
		_contains_any_phrase(text, ("approve", "approved"))
		and _contains_any_phrase(text, ("as", "for"))
		and _contains_any_phrase(text, ("customer", "supplier", "vendor", "product", "item", "catalog", "list"))
	):
		return False
	has_mutation_target = _has_target_family(targets, {"cust", "sup", "sinv"}) or _contains_any_phrase(
		text,
		_MUTATION_TARGETS,
	)
	if not has_mutation_target:
		return False
	if _contains_any_phrase(text, _MUTATION_ACTION_TERMS):
		return True
	return _contains_any_phrase(text, _ACCOUNTING_ACTION_SIGNALS) and _contains_any_phrase(text, _MUTATION_TARGETS)


def _looks_like_accounting_valuation_obsolescence_domain(text: str, targets: Dict[str, Any]) -> bool:
	has_item_context = _has_target_family(targets, {"item"})
	if not has_item_context:
		return False
	if _contains_any_phrase(text, _ACCOUNTING_VALUATION_OBSOLESCENCE_SIGNALS):
		return True
	return _contains_any_phrase(text, _ACCOUNTING_VALUATION_CONTEXT) and detect_decision_question_mode(text)


def _looks_like_pricing_discount_valuation_domain(text: str, targets: Dict[str, Any]) -> bool:
	has_item_context = _has_target_family(targets, {"item"})
	if not has_item_context or not detect_decision_question_mode(text):
		return False
	if _contains_ordered_phrase_groups(text, (("mark",), ("down",))):
		return True
	if _contains_any_phrase(text, _PRICING_DISCOUNT_VALUATION_SIGNALS):
		return True
	return _contains_any_phrase(text, _PRICING_DISCOUNT_VALUATION_CONTEXT)


def _looks_like_true_followup(text: str) -> bool:
	if re.search(r"\bwhat\s+about\s+(last|this|next)\s+(month|week|quarter|year)\b", text):
		return True
	if re.search(r"\b(additional\s+)?details?\s+about\b.*\branked\b", text):
		return True
	if (
		_contains_any_phrase(text, ("why is", "why are"))
		and _contains_any_phrase(
			text,
			(
				"this customer",
				"that customer",
				"this supplier",
				"that supplier",
				"this vendor",
				"that vendor",
				"this product",
				"that product",
				"this item",
				"that item",
				"this invoice",
				"that invoice",
				"this row",
				"that row",
			),
		)
		and _contains_any_phrase(text, ("risky", "concerning", "overdue", "high", "low", "large", "important"))
	):
		return True
	has_context_reference = _contains_any_phrase(text, _TRUE_FOLLOWUP_CONTEXT_REFERENCES)
	if not has_context_reference:
		return False
	if _contains_any_phrase(text, _READ_ONLY_FOLLOWUP_INTENTS):
		return True
	if re.search(r"\bfrom\s+that\s+list\b.*\b(show|oldest|newest|largest|smallest|unpaid|overdue|one)\b", text):
		return True
	if re.search(r"\bshow\s+the\s+same\s+for\b", text):
		return True
	if re.search(r"\b(give|provide|show)\s+(me\s+)?more\s+details?\s+about\s+(this|that)\b", text):
		return True
	if re.search(r"\bbreak(ing)?\s+down\s+details?\b", text):
		return True
	if _contains_phrase(text, "this invoice") and _contains_any_phrase(text, ("overdue", "paid", "unpaid", "due")):
		return True
	return False


def detect_business_action_domain(text: str) -> str:
	targets = extract_erp_targets(text)

	if _contains_any_phrase(text, _LEGAL_SIGNALS):
		return DOMAIN_LEGAL_REGULATORY

	if _looks_like_report_hiding_domain(text, targets):
		return DOMAIN_REPORT_HIDING_MANIPULATION

	if _looks_like_payment_delay_domain(text, targets):
		return DOMAIN_PAYMENT_DELAY_WITHHOLDING

	if _looks_like_write_mutation_domain(text, targets):
		return DOMAIN_WRITE_MUTATION_ACTION

	if _looks_like_pricing_discount_valuation_domain(text, targets):
		return DOMAIN_PRICING_DISCOUNT_VALUATION_DECISION

	if _looks_like_accounting_valuation_obsolescence_domain(text, targets):
		return DOMAIN_ACCOUNTING_VALUATION_OBSOLESCENCE_LIFECYCLE

	if _has_target_family(targets, {"item"}) and _contains_any_phrase(text, _INVENTORY_DISPOSAL_SIGNALS):
		return DOMAIN_INVENTORY_LEVEL_DISPOSAL_OBSOLESCENCE

	if _has_target_family(targets, {"item"}) and _contains_any_phrase(text, _PROCUREMENT_ORDERING_SIGNALS):
		return DOMAIN_PROCUREMENT_ORDERING_RESTOCKING

	if _has_target_family(targets, {"item"}) and _contains_any_phrase(text, _PRODUCT_CATALOG_LIFECYCLE_SIGNALS):
		return DOMAIN_PRODUCT_CATALOG_LIFECYCLE

	if _has_target_family(targets, {"cust", "sup"}) and _contains_any_phrase(
		text,
		_CUSTOMER_SUPPLIER_RETENTION_SIGNALS,
	):
		return DOMAIN_CUSTOMER_SUPPLIER_ADMISSION_RETENTION

	return DOMAIN_NONE


def _decision(
	*,
	category: str,
	required_answer_mode: str,
	boundary_reason: str,
	message: str,
	context_reuse_allowed: bool = False,
	report_routing_allowed: bool = False,
) -> UserIntentBoundaryDecision:
	return UserIntentBoundaryDecision(
		category=category,
		context_reuse_allowed=context_reuse_allowed,
		report_routing_allowed=report_routing_allowed,
		required_answer_mode=required_answer_mode,
		boundary_reason=boundary_reason,
		original_user_text_hash=_message_hash(message),
	)


def _decision_for_business_domain(domain: str, raw_message: str) -> UserIntentBoundaryDecision | None:
	if domain == DOMAIN_NONE:
		return None
	if domain == DOMAIN_LEGAL_REGULATORY:
		return _decision(
			category=CATEGORY_LEGAL_OR_REGULATORY_ADVICE,
			required_answer_mode=ANSWER_MODE_POLICY_BOUNDARY,
			boundary_reason="legal_or_regulatory_domain_requires_boundary",
			message=raw_message,
		)
	if domain == DOMAIN_REPORT_HIDING_MANIPULATION:
		return _decision(
			category=CATEGORY_FRAUD_OR_MANIPULATION,
			required_answer_mode=ANSWER_MODE_POLICY_BOUNDARY,
			boundary_reason="report_hiding_manipulation_domain_blocked",
			message=raw_message,
		)
	if domain in {DOMAIN_WRITE_MUTATION_ACTION, DOMAIN_ACCOUNTING_WRITEOFF_ADJUSTMENT}:
		return _decision(
			category=CATEGORY_WRITE_OR_MUTATION_ACTION,
			required_answer_mode=ANSWER_MODE_CONTROL_BOUNDARY,
			boundary_reason=f"{domain}_requires_control_boundary",
			message=raw_message,
		)
	return _decision(
		category=CATEGORY_RECOMMENDATION_OR_BUSINESS_ADVICE,
		required_answer_mode=ANSWER_MODE_POLICY_BOUNDARY,
		boundary_reason=f"{domain}_requires_policy_boundary",
		message=raw_message,
	)


def classify_user_intent_boundary(message: Any) -> UserIntentBoundaryDecision:
	text = normalize_user_text(message)
	raw_message = str(message or "")

	if not text:
		return _decision(
			category=CATEGORY_CLARIFICATION_REQUIRED,
			required_answer_mode=ANSWER_MODE_CLARIFICATION,
			boundary_reason="empty_message_requires_clarification",
			message=raw_message,
		)

	targets = extract_erp_targets(text)
	safe_lookup = detect_safe_factual_lookup(text)
	decision_mode = detect_decision_question_mode(text)
	business_domain = detect_business_action_domain(text)

	if _looks_like_prediction(text):
		return _decision(
			category=CATEGORY_PREDICTION_OR_FORECAST,
			required_answer_mode=ANSWER_MODE_POLICY_BOUNDARY,
			boundary_reason="prediction_or_forecast_requires_approved_policy",
			message=raw_message,
		)

	if business_domain != DOMAIN_NONE and (targets["has_target"] or decision_mode or not safe_lookup):
		domain_decision = _decision_for_business_domain(business_domain, raw_message)
		if domain_decision is not None:
			return domain_decision

	if _looks_like_unsupported_decision(text):
		return _decision(
			category=CATEGORY_UNSUPPORTED_DECISION_REQUEST,
			required_answer_mode=ANSWER_MODE_POLICY_BOUNDARY,
			boundary_reason="unsupported_decision_request_requires_owner_policy",
			message=raw_message,
		)

	if _looks_like_true_followup(text):
		return _decision(
			category=CATEGORY_TRUE_FOLLOWUP,
			context_reuse_allowed=True,
			report_routing_allowed=True,
			required_answer_mode=ANSWER_MODE_GOVERNED_ERP,
			boundary_reason="explicit_safe_followup",
			message=raw_message,
		)

	if decision_mode and targets["has_target"] and not safe_lookup:
		return _decision(
			category=CATEGORY_CLARIFICATION_REQUIRED,
			required_answer_mode=ANSWER_MODE_CLARIFICATION,
			boundary_reason="targeted_decision_request_requires_clarification",
			message=raw_message,
		)

	if _matches_any(_AMBIGUOUS_FOLLOWUP_PATTERNS, text):
		return _decision(
			category=CATEGORY_AMBIGUOUS_FOLLOWUP,
			required_answer_mode=ANSWER_MODE_CLARIFICATION,
			boundary_reason="ambiguous_followup_requires_clarification",
			message=raw_message,
		)

	if _matches_any(_CLARIFICATION_PATTERNS, text):
		return _decision(
			category=CATEGORY_CLARIFICATION_REQUIRED,
			required_answer_mode=ANSWER_MODE_CLARIFICATION,
			boundary_reason="missing_or_ambiguous_business_context",
			message=raw_message,
		)

	if safe_lookup:
		return _decision(
			category=CATEGORY_FACTUAL_ERP_QUERY,
			report_routing_allowed=True,
			required_answer_mode=ANSWER_MODE_GOVERNED_ERP,
			boundary_reason="safe_factual_erp_query",
			message=raw_message,
		)

	return _decision(
		category=CATEGORY_CLARIFICATION_REQUIRED,
		required_answer_mode=ANSWER_MODE_CLARIFICATION,
		boundary_reason="unrecognized_or_underspecified_business_request",
		message=raw_message,
	)


def build_user_intent_boundary_contract(message: Any) -> Dict[str, Any]:
	return classify_user_intent_boundary(message).to_payload()


def validate_user_intent_boundary_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
	missing_fields: List[str] = []
	invalid_fields: List[str] = []
	if not isinstance(payload, dict):
		return {"valid": False, "missing_fields": [], "invalid_fields": ["payload"]}

	required_fields = (
		"category",
		"context_reuse_allowed",
		"report_routing_allowed",
		"required_answer_mode",
		"boundary_reason",
		"source",
		"contract_version",
	)
	for field in required_fields:
		if field not in payload:
			missing_fields.append(field)

	category = str(payload.get("category") or "").strip()
	answer_mode = str(payload.get("required_answer_mode") or "").strip()
	if category and category not in ALLOWED_USER_INTENT_BOUNDARY_CATEGORIES:
		invalid_fields.append("category")
	if answer_mode and answer_mode not in ALLOWED_USER_INTENT_BOUNDARY_ANSWER_MODES:
		invalid_fields.append("required_answer_mode")
	if payload.get("source") != USER_INTENT_BOUNDARY_SOURCE:
		invalid_fields.append("source")
	if payload.get("contract_version") != CONTRACT_VERSION:
		invalid_fields.append("contract_version")
	if not isinstance(payload.get("context_reuse_allowed"), bool):
		invalid_fields.append("context_reuse_allowed")
	if not isinstance(payload.get("report_routing_allowed"), bool):
		invalid_fields.append("report_routing_allowed")

	if category in {
		CATEGORY_PREDICTION_OR_FORECAST,
		CATEGORY_RECOMMENDATION_OR_BUSINESS_ADVICE,
		CATEGORY_LEGAL_OR_REGULATORY_ADVICE,
		CATEGORY_FRAUD_OR_MANIPULATION,
		CATEGORY_UNSUPPORTED_DECISION_REQUEST,
	}:
		if answer_mode != ANSWER_MODE_POLICY_BOUNDARY:
			invalid_fields.append("required_answer_mode_for_policy_boundary_category")
		if payload.get("context_reuse_allowed") is not False:
			invalid_fields.append("context_reuse_allowed_for_boundary_category")
		if payload.get("report_routing_allowed") is not False:
			invalid_fields.append("report_routing_allowed_for_boundary_category")

	if category == CATEGORY_WRITE_OR_MUTATION_ACTION:
		if answer_mode != ANSWER_MODE_CONTROL_BOUNDARY:
			invalid_fields.append("required_answer_mode_for_write_action")
		if payload.get("context_reuse_allowed") is not False:
			invalid_fields.append("context_reuse_allowed_for_write_action")
		if payload.get("report_routing_allowed") is not False:
			invalid_fields.append("report_routing_allowed_for_write_action")

	if category == CATEGORY_TRUE_FOLLOWUP:
		if payload.get("context_reuse_allowed") is not True:
			invalid_fields.append("context_reuse_allowed_for_true_followup")
		if payload.get("report_routing_allowed") is not True:
			invalid_fields.append("report_routing_allowed_for_true_followup")

	return {
		"valid": not missing_fields and not invalid_fields,
		"missing_fields": missing_fields,
		"invalid_fields": invalid_fields,
	}
