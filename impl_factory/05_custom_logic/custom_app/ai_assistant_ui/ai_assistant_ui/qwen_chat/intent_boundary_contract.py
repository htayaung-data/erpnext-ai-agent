from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional, Tuple


CONTRACT_VERSION = "v1-ib-a.1"
TRACE_REDACTION_SAFE = "safe"

ANSWER_MODE_GOVERNED_ERP = "governed_erp_answer"
ANSWER_MODE_CLARIFICATION = "clarification"
ANSWER_MODE_POLICY_BOUNDARY = "policy_boundary"
ANSWER_MODE_CONTROL_BOUNDARY = "control_boundary"

VALID_ANSWER_MODES = {
	ANSWER_MODE_GOVERNED_ERP,
	ANSWER_MODE_CLARIFICATION,
	ANSWER_MODE_POLICY_BOUNDARY,
	ANSWER_MODE_CONTROL_BOUNDARY,
}

CLAUSE_TYPE_FACTUAL_LOOKUP = "factual_lookup"
CLAUSE_TYPE_SAFE_FOLLOWUP = "safe_followup"
CLAUSE_TYPE_BUSINESS_ACTION = "business_action"
CLAUSE_TYPE_POLICY_BOUNDARY = "policy_boundary"
CLAUSE_TYPE_AMBIGUOUS = "ambiguous"

VALID_CLAUSE_TYPES = {
	CLAUSE_TYPE_FACTUAL_LOOKUP,
	CLAUSE_TYPE_SAFE_FOLLOWUP,
	CLAUSE_TYPE_BUSINESS_ACTION,
	CLAUSE_TYPE_POLICY_BOUNDARY,
	CLAUSE_TYPE_AMBIGUOUS,
}

TARGET_TYPE_CUSTOMER = "customer"
TARGET_TYPE_SUPPLIER = "supplier"
TARGET_TYPE_ITEM = "item"
TARGET_TYPE_INVOICE = "invoice"
TARGET_TYPE_REPORT = "report"
TARGET_TYPE_PAYMENT = "payment"
TARGET_TYPE_ACCOUNTING_ENTRY = "accounting_entry"

VALID_TARGET_TYPES = {
	TARGET_TYPE_CUSTOMER,
	TARGET_TYPE_SUPPLIER,
	TARGET_TYPE_ITEM,
	TARGET_TYPE_INVOICE,
	TARGET_TYPE_REPORT,
	TARGET_TYPE_PAYMENT,
	TARGET_TYPE_ACCOUNTING_ENTRY,
}

REFERENCE_TYPE_PRONOUN = "pronoun"
REFERENCE_TYPE_THIS_THAT = "this_that"
REFERENCE_TYPE_VISIBLE_ROW = "visible_row"
REFERENCE_TYPE_PREVIOUS_CONTEXT = "previous_context"

VALID_REFERENCE_TYPES = {
	REFERENCE_TYPE_PRONOUN,
	REFERENCE_TYPE_THIS_THAT,
	REFERENCE_TYPE_VISIBLE_ROW,
	REFERENCE_TYPE_PREVIOUS_CONTEXT,
}

REFERENCE_RESOLVED = "resolved"
REFERENCE_UNRESOLVED = "unresolved"
REFERENCE_NOT_REQUIRED = "not_required"

VALID_REFERENCE_STATUSES = {
	REFERENCE_RESOLVED,
	REFERENCE_UNRESOLVED,
	REFERENCE_NOT_REQUIRED,
}

DOMAIN_PRICING_VALUATION_ACTION = "pricing_valuation_action"
DOMAIN_CUSTOMER_SUPPLIER_RETENTION_ADMISSION = "customer_supplier_retention_admission"
DOMAIN_PRODUCT_CATALOG_LIFECYCLE = "product_catalog_lifecycle"
DOMAIN_INVENTORY_STOCKING_DISPOSAL = "inventory_stocking_disposal"
DOMAIN_PAYMENT_DELAY_WITHHOLDING_RELEASE = "payment_delay_withholding_release"
DOMAIN_REPORT_HIDING_OR_MANIPULATION = "report_hiding_or_manipulation"
DOMAIN_ACCOUNTING_WRITEOFF_ADJUSTMENT = "accounting_writeoff_adjustment"
DOMAIN_RECORD_MUTATION_OR_WORKFLOW_ACTION = "record_mutation_or_workflow_action"
DOMAIN_PREDICTION_SCORE_OR_FUTURE_CAUSE = "prediction_score_or_future_cause"
DOMAIN_LEGAL_OR_REGULATORY_ADVICE = "legal_or_regulatory_advice"
DOMAIN_UNSUPPORTED_BUSINESS_RECOMMENDATION = "unsupported_business_recommendation"
DOMAIN_NONE = "none"

VALID_BUSINESS_ACTION_DOMAINS = {
	DOMAIN_PRICING_VALUATION_ACTION,
	DOMAIN_CUSTOMER_SUPPLIER_RETENTION_ADMISSION,
	DOMAIN_PRODUCT_CATALOG_LIFECYCLE,
	DOMAIN_INVENTORY_STOCKING_DISPOSAL,
	DOMAIN_PAYMENT_DELAY_WITHHOLDING_RELEASE,
	DOMAIN_REPORT_HIDING_OR_MANIPULATION,
	DOMAIN_ACCOUNTING_WRITEOFF_ADJUSTMENT,
	DOMAIN_RECORD_MUTATION_OR_WORKFLOW_ACTION,
	DOMAIN_PREDICTION_SCORE_OR_FUTURE_CAUSE,
	DOMAIN_LEGAL_OR_REGULATORY_ADVICE,
	DOMAIN_UNSUPPORTED_BUSINESS_RECOMMENDATION,
	DOMAIN_NONE,
}

POLICY_DOMAINS = {
	DOMAIN_REPORT_HIDING_OR_MANIPULATION,
	DOMAIN_PREDICTION_SCORE_OR_FUTURE_CAUSE,
	DOMAIN_LEGAL_OR_REGULATORY_ADVICE,
	DOMAIN_UNSUPPORTED_BUSINESS_RECOMMENDATION,
}

CONTROL_DOMAINS = {
	DOMAIN_ACCOUNTING_WRITEOFF_ADJUSTMENT,
	DOMAIN_RECORD_MUTATION_OR_WORKFLOW_ACTION,
}

PROPOSER_ROLE_LIGHTWEIGHT = "lightweight_intent_proposer"
PROPOSER_STATUS_COMPLETE = "complete"
PROPOSER_OUTPUT_VALID = "valid"
DETERMINISTIC_VALIDATOR_VALID = "valid"
DETERMINISTIC_VALIDATOR_INVALID = "invalid"
SEMANTIC_BACKSTOP_MISSING = "missing"
SEMANTIC_BACKSTOP_SAFE = "safe"
SEMANTIC_BACKSTOP_UNSAFE = "unsafe"
SEMANTIC_BACKSTOP_AMBIGUOUS = "ambiguous"

AUTHORITY_SOURCE_DETERMINISTIC_VALIDATOR = "deterministic_validator"
AUTHORITY_SOURCE_STRICT_DETERMINISTIC_SAFE_SUBSET = "strict_deterministic_safe_subset"
AUTHORITY_DECISION_ALLOW_REPORT = "allow_report"
AUTHORITY_DECISION_BOUNDARY = "boundary"
AUTHORITY_DECISION_CLARIFICATION = "clarification"
AUTHORITY_DECISION_BLOCK = "block"

MIN_PROPOSER_CONFIDENCE = 0.75

PROPOSAL_SOURCE_LIGHTWEIGHT_MODEL = "lightweight_model_structured_proposal"
PROPOSAL_SOURCE_DETERMINISTIC_SAFE_SUBSET = "deterministic_safe_subset_mechanical_validator"
PROPOSAL_SOURCE_SEMANTIC_BACKSTOP = "semantic_backstop_restrict_only"
PROPOSAL_SOURCE_LEXICAL_ALARM = "lexical_alarm_restrict_only"

LEXICAL_AUTHORITY_EFFECT_NONE = "none"
LEXICAL_AUTHORITY_EFFECT_RESTRICT_ONLY = "restrict_only"

COMPLETENESS_STATUS_COMPLETE = "complete"
AUDIT_STATUS_PASSED = "passed"
FULL_SPAN_FACTUAL_AUTHORITY_MECHANICAL_ONLY = "mechanical_only"
FULL_SPAN_FACTUAL_AUTHORITY_NOT_ALLOWED = "not_allowed"
VERIFIER_AUTHORITY_EFFECT_CONSISTENCY_ONLY = "consistency_evidence_only"
ROLE_DISAGREEMENT_POLICY_FAIL_CLOSED = "fail_closed"
NATURAL_LANGUAGE_REPORT_AUTHORITY_BLOCKED_WITHOUT_VERIFIER = "blocked_without_independent_verifier"
NATURAL_LANGUAGE_REPORT_AUTHORITY_VERIFIED = "verified_by_independent_clause_role_guard"
VERIFIER_PROVENANCE_TRUSTED = "trusted_validator_owned_registry"
VERIFIER_PROVENANCE_UNTRUSTED = "untrusted_or_unverified"
VERIFIER_PAYLOAD_HASH_MATCHED = "matched"
VERIFIER_PAYLOAD_HASH_FAILED = "failed"
VERIFIER_ATTESTATION_VERIFIED = "verified"
VERIFIER_ATTESTATION_FAILED = "failed"
ROLE_VERIFICATION_AUTHORITY_EFFECT_CONSISTENCY_ONLY = "consistency_evidence_only"
SEMANTIC_BACKSTOP_AUTHORITY_EFFECT_RESTRICT_ONLY = "restrict_only"
LEXICAL_EVIDENCE_AUTHORITY_EFFECT_RESTRICT_ONLY = "restrict_only"
VALIDATOR_SAFE_ROUTE_BLOCKED_WITHOUT_PROOF = "blocked_without_validator_safety_proof"
VALIDATOR_SAFE_ROUTE_PROVEN = "validator_safe_route_proven"
VALIDATOR_OWNED_SAFETY_PROOF_SOURCE = "validator_owned_safety_proof_registry"
VALIDATOR_OWNED_SAFETY_PROOF_VERSION = "v1-ib-a-j.1"
VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_SOURCE = "validator_owned_raw_message_safety_analyzer"
VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_PROOF_VERSION = "v1-ib-a-k.1"
VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_SOURCE = "validator_owned_raw_message_analysis_registry"
VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_VERSION = "v1-ib-a-n.1"
VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_SOURCE = "validator_owned_raw_message_analyzer_execution"
VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_VERSION = "v1-ib-a-o.1"
VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_SOURCE = "validator_owned_replayed_raw_message_safety"
VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_VERSION = "v1-ib-a-p.1"
RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE = "non_derivative_raw_message_safety_analysis"
SAFETY_PROOF_ATTESTATION_VERIFIED = "verified"
SAFETY_PROOF_ATTESTATION_FAILED = "failed"

APPROVED_FULL_SPAN_FACTUAL_ALLOW_REASONS = {
	"preapproved_mechanical_command",
}

# Empty by design for V1-IB-A-F: no normal natural-language prompt can
# self-promote into a mechanical command. Future entries must be code-owned.
VALIDATOR_OWNED_MECHANICAL_COMMAND_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Empty by default for production. Tests may inject a local fixture registry,
# but verifier authority must always come from validator-owned registry state.
VALIDATOR_OWNED_TRUSTED_VERIFIER_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Empty by default for production. Report routing needs a validator-owned
# proof entry; proposer, verifier, semantic, and lexical evidence cannot
# create this proof by themselves.
VALIDATOR_OWNED_SAFETY_PROOF_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Empty by default for production. Tests may inject local fixture entries by
# mutating this validator-owned module state; caller-supplied registries are
# not route authority.
VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Empty by default for production. A signed proof can only authorize routing
# when this validator-owned state independently supports the same raw-message
# safety conclusions and evidence hashes.
VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_REGISTRY: Dict[str, Dict[str, Any]] = {}

# Empty by default for production. Analysis registry entries are assertions
# unless backed by a validator-owned executed analyzer record.
VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_REGISTRY: Dict[str, Dict[str, Any]] = {}

RAW_MESSAGE_ANALYSIS_INPUT_FIELDS = (
	"raw_message_hash",
	"normalized_message_hash",
	"raw_message_analysis_subject_hash",
)

REQUIRED_RAW_MESSAGE_ANALYSIS_FIELDS = (
	"registry_status",
	"raw_message_hash",
	"normalized_message_hash",
	"raw_message_analysis_subject_hash",
	"analysis_source",
	"analysis_version",
	"analysis_status",
	"validator_safety_analyzer_id",
	"validator_safety_analyzer_version",
	"raw_message_clause_coverage_status",
	"raw_message_secondary_intent_status",
	"raw_message_mixed_intent_status",
	"raw_message_residual_status",
	"raw_message_connector_status",
	"raw_message_reference_status",
	"raw_message_unsafe_ambiguity_status",
	"raw_message_clause_coverage_evidence_hash",
	"raw_message_secondary_intent_evidence_hash",
	"raw_message_mixed_intent_evidence_hash",
	"raw_message_residual_evidence_hash",
	"raw_message_connector_evidence_hash",
	"raw_message_reference_evidence_hash",
	"raw_message_unsafe_ambiguity_evidence_hash",
	"analysis_basis",
	"derived_from_proposer_roles",
	"derived_from_verifier_roles",
	"derived_from_semantic_safe_output",
	"derived_from_lexical_phrase_authority",
	"trace_redaction_status",
)

CANONICAL_RAW_MESSAGE_ANALYSIS_FIELDS = REQUIRED_RAW_MESSAGE_ANALYSIS_FIELDS

REQUIRED_RAW_MESSAGE_ANALYSIS_EXECUTION_FIELDS = (
	"registry_status",
	"raw_message_hash",
	"normalized_message_hash",
	"analyzer_id",
	"analyzer_version",
	"run_id",
	"input_hash",
	"output_hash",
	"artifact_hash",
	"execution_source",
	"execution_version",
	"execution_mode",
	"execution_status",
	"trace_redaction_status",
	"replay_status",
	"execution_payload_hash",
	"attestation",
)

CANONICAL_RAW_MESSAGE_ANALYSIS_EXECUTION_FIELDS = tuple(
	field_name for field_name in REQUIRED_RAW_MESSAGE_ANALYSIS_EXECUTION_FIELDS if field_name not in {"execution_payload_hash", "attestation"}
)

REQUIRED_RAW_MESSAGE_SAFETY_PROOF_FIELDS = (
	"safety_proof_id",
	"safety_proof_subject_hash",
	"raw_message_hash",
	"normalized_message_hash",
	"validator_safety_analyzer_id",
	"validator_safety_analyzer_version",
	"raw_message_safety_status",
	"raw_message_clause_coverage_status",
	"raw_message_secondary_intent_status",
	"raw_message_mixed_intent_status",
	"raw_message_residual_status",
	"raw_message_reference_status",
	"raw_message_safety_evidence_hash",
	"raw_message_clause_boundary_evidence_hash",
	"raw_message_secondary_intent_evidence_hash",
	"raw_message_residual_evidence_hash",
	"raw_message_reference_evidence_hash",
	"raw_message_clause_coverage_evidence",
	"raw_message_secondary_intent_evidence",
	"raw_message_mixed_intent_evidence",
	"raw_message_residual_evidence",
	"raw_message_connector_evidence",
	"raw_message_reference_evidence",
	"raw_message_unsafe_ambiguity_evidence",
	"safe_route_authority",
	"safety_proof_basis",
	"safety_proof_payload_hash",
	"safety_proof_attestation",
	"trace_redaction_status",
)

CANONICAL_RAW_MESSAGE_SAFETY_PROOF_FIELDS = (
	"safety_proof_subject_hash",
	"raw_message_hash",
	"normalized_message_hash",
	"validator_safety_analyzer_id",
	"validator_safety_analyzer_version",
	"raw_message_safety_status",
	"raw_message_clause_coverage_status",
	"raw_message_secondary_intent_status",
	"raw_message_mixed_intent_status",
	"raw_message_residual_status",
	"raw_message_reference_status",
	"raw_message_safety_evidence_hash",
	"raw_message_clause_boundary_evidence_hash",
	"raw_message_secondary_intent_evidence_hash",
	"raw_message_residual_evidence_hash",
	"raw_message_reference_evidence_hash",
	"raw_message_clause_coverage_evidence",
	"raw_message_secondary_intent_evidence",
	"raw_message_mixed_intent_evidence",
	"raw_message_residual_evidence",
	"raw_message_connector_evidence",
	"raw_message_reference_evidence",
	"raw_message_unsafe_ambiguity_evidence",
	"safe_route_authority",
	"safety_proof_basis",
	"trace_redaction_status",
)

REQUIRED_RAW_MESSAGE_SAFETY_EVIDENCE_FIELDS = (
	"evidence_id",
	"evidence_type",
	"evidence_status",
	"evidence_basis",
	"evidence_hash",
	"source_analyzer_id",
	"source_analyzer_version",
	"derived_from_proposer_roles",
	"derived_from_verifier_roles",
	"derived_from_semantic_safe_output",
	"derived_from_lexical_phrase_authority",
	"redaction_status",
	"blocking_reason",
)

CANONICAL_RAW_MESSAGE_SAFETY_EVIDENCE_FIELDS = tuple(
	field_name for field_name in REQUIRED_RAW_MESSAGE_SAFETY_EVIDENCE_FIELDS if field_name != "evidence_hash"
)

RAW_MESSAGE_SAFETY_EVIDENCE_REQUIREMENTS = {
	"raw_message_clause_coverage_evidence": {
		"evidence_type": "clause_coverage",
		"evidence_status": "complete",
		"proof_status_field": "raw_message_clause_coverage_status",
	},
	"raw_message_secondary_intent_evidence": {
		"evidence_type": "secondary_intent",
		"evidence_status": "none",
		"proof_status_field": "raw_message_secondary_intent_status",
	},
	"raw_message_mixed_intent_evidence": {
		"evidence_type": "mixed_intent",
		"evidence_status": "none",
		"proof_status_field": "raw_message_mixed_intent_status",
	},
	"raw_message_residual_evidence": {
		"evidence_type": "residual",
		"evidence_status": "clear",
		"proof_status_field": "raw_message_residual_status",
	},
	"raw_message_connector_evidence": {
		"evidence_type": "connector",
		"evidence_status": "accounted",
		"proof_status_field": "",
	},
	"raw_message_reference_evidence": {
		"evidence_type": "reference",
		"evidence_status": "resolved_or_not_required",
		"proof_status_field": "raw_message_reference_status",
	},
	"raw_message_unsafe_ambiguity_evidence": {
		"evidence_type": "unsafe_ambiguity",
		"evidence_status": "none",
		"proof_status_field": "",
	},
}

RAW_MESSAGE_SAFETY_EVIDENCE_HASH_FIELDS = {
	"raw_message_unsafe_ambiguity_evidence": "raw_message_safety_evidence_hash",
	"raw_message_clause_coverage_evidence": "raw_message_clause_boundary_evidence_hash",
	"raw_message_secondary_intent_evidence": "raw_message_secondary_intent_evidence_hash",
	"raw_message_residual_evidence": "raw_message_residual_evidence_hash",
	"raw_message_reference_evidence": "raw_message_reference_evidence_hash",
}

UNSAFE_EVIDENCE_STATUSES = {"unsupported", "unknown", "ambiguous", "unsafe", "contradictory"}

FORBIDDEN_LEXICAL_PROPOSER_IDENTIFIERS = {
	"regex_classifier",
	"keyword_classifier",
	"pattern_classifier",
	"handcrafted_lexical_classifier",
}

REQUIRED_PROPOSAL_FIELDS = (
	"intent_proposer_role",
	"intent_proposer_status",
	"intent_proposer_confidence",
	"intent_proposer_model_name",
	"intent_proposer_output_status",
	"proposal_authority_source",
	"proposal_completeness_status",
	"clause_segmentation_status",
	"secondary_intent_audit_status",
	"residual_audit_status",
	"clause_role_confidence_status",
	"full_span_factual_authority",
	"full_span_factual_allow_reason",
	"natural_language_interpretation_required",
	"independent_parse_guard_status",
	"clause_count",
	"clauses",
	"erp_targets",
	"visible_context_references",
	"mixed_intent_detected",
	"trace_redaction_status",
)

REQUIRED_CLAUSE_FIELDS = (
	"clause_id",
	"index",
	"start",
	"end",
	"clause_type",
	"factual_lookup_intent",
	"safe_followup_intent",
	"decision_intent",
	"advice_intent",
	"business_action_intent",
	"policy_boundary_intent",
	"business_action_domain",
	"policy_domain",
	"ambiguity_status",
)

REQUIRED_CLAUSE_VERIFICATION_FIELDS = (
	"verified_clause_type",
	"verified_factual_lookup_intent",
	"verified_safe_followup_intent",
	"verified_decision_intent",
	"verified_advice_intent",
	"verified_business_action_intent",
	"verified_policy_boundary_intent",
	"verified_business_action_domain",
	"verified_policy_domain",
	"verification_status",
	"verification_confidence",
	"verification_blocking_reason",
)

REQUIRED_VERIFIER_ENVELOPE_FIELDS = (
	"envelope_version",
	"raw_message_hash",
	"normalized_message_hash",
	"verifier_source",
	"verifier_run_id",
	"verifier_model_name",
	"verifier_prompt_version",
	"verifier_status",
	"verifier_independence_status",
	"verifier_authority_effect",
	"verifier_payload_hash",
	"verifier_attestation",
	"trace_redaction_status",
	"verified_clauses",
)

CANONICAL_VERIFIER_PAYLOAD_FIELDS = (
	"envelope_version",
	"raw_message_hash",
	"normalized_message_hash",
	"verifier_source",
	"verifier_run_id",
	"verifier_model_name",
	"verifier_prompt_version",
	"verifier_status",
	"verifier_independence_status",
	"verifier_authority_effect",
	"trace_redaction_status",
	"verified_clauses",
)

REQUIRED_VERIFIED_CLAUSE_FIELDS = (
	"clause_id",
	"span_start",
	"span_end",
	"normalized_clause_hash",
	"verified_clause_type",
	"verified_factual_lookup_intent",
	"verified_safe_followup_intent",
	"verified_decision_intent",
	"verified_advice_intent",
	"verified_business_action_intent",
	"verified_policy_boundary_intent",
	"verified_business_action_domain",
	"verified_policy_domain",
	"verification_status",
	"verification_confidence",
	"verification_blocking_reason",
)

REQUIRED_TARGET_FIELDS = ("target_id", "target_type", "value", "schema_status")
REQUIRED_REFERENCE_FIELDS = (
	"reference_id",
	"reference_type",
	"resolution_status",
	"read_only_intent",
)


@dataclass(frozen=True)
class OntologyDomainDefinition:
	name: str
	target_types: Tuple[str, ...]
	route_family: str
	unsafe_for_report_routing: bool
	description: str


ONTOLOGY_DOMAIN_DEFINITIONS: Dict[str, OntologyDomainDefinition] = {
	DOMAIN_PRICING_VALUATION_ACTION: OntologyDomainDefinition(
		name=DOMAIN_PRICING_VALUATION_ACTION,
		target_types=(TARGET_TYPE_ITEM,),
		route_family="policy_boundary",
		unsafe_for_report_routing=True,
		description="Pricing, discount, valuation, markdown, or repricing decision intent.",
	),
	DOMAIN_CUSTOMER_SUPPLIER_RETENTION_ADMISSION: OntologyDomainDefinition(
		name=DOMAIN_CUSTOMER_SUPPLIER_RETENTION_ADMISSION,
		target_types=(TARGET_TYPE_CUSTOMER, TARGET_TYPE_SUPPLIER),
		route_family="policy_boundary",
		unsafe_for_report_routing=True,
		description="Customer or supplier admission, retention, removal, or list-membership decision intent.",
	),
	DOMAIN_PRODUCT_CATALOG_LIFECYCLE: OntologyDomainDefinition(
		name=DOMAIN_PRODUCT_CATALOG_LIFECYCLE,
		target_types=(TARGET_TYPE_ITEM,),
		route_family="policy_boundary",
		unsafe_for_report_routing=True,
		description="Product catalog, sale availability, lifecycle, continuation, or discontinuation decision intent.",
	),
	DOMAIN_INVENTORY_STOCKING_DISPOSAL: OntologyDomainDefinition(
		name=DOMAIN_INVENTORY_STOCKING_DISPOSAL,
		target_types=(TARGET_TYPE_ITEM,),
		route_family="policy_boundary",
		unsafe_for_report_routing=True,
		description="Inventory level, stocking, procurement, restocking, disposal, or obsolescence decision intent.",
	),
	DOMAIN_PAYMENT_DELAY_WITHHOLDING_RELEASE: OntologyDomainDefinition(
		name=DOMAIN_PAYMENT_DELAY_WITHHOLDING_RELEASE,
		target_types=(TARGET_TYPE_SUPPLIER, TARGET_TYPE_PAYMENT),
		route_family="policy_boundary",
		unsafe_for_report_routing=True,
		description="Payment delay, withholding, release, or non-payment decision intent.",
	),
	DOMAIN_REPORT_HIDING_OR_MANIPULATION: OntologyDomainDefinition(
		name=DOMAIN_REPORT_HIDING_OR_MANIPULATION,
		target_types=(TARGET_TYPE_INVOICE, TARGET_TYPE_REPORT),
		route_family="policy_boundary",
		unsafe_for_report_routing=True,
		description="Report hiding, omission, concealment, or manipulation intent.",
	),
	DOMAIN_ACCOUNTING_WRITEOFF_ADJUSTMENT: OntologyDomainDefinition(
		name=DOMAIN_ACCOUNTING_WRITEOFF_ADJUSTMENT,
		target_types=(TARGET_TYPE_INVOICE, TARGET_TYPE_ITEM, TARGET_TYPE_ACCOUNTING_ENTRY),
		route_family="control_boundary",
		unsafe_for_report_routing=True,
		description="Accounting write-off, adjustment, reversal, journal, or valuation posting intent.",
	),
	DOMAIN_RECORD_MUTATION_OR_WORKFLOW_ACTION: OntologyDomainDefinition(
		name=DOMAIN_RECORD_MUTATION_OR_WORKFLOW_ACTION,
		target_types=(TARGET_TYPE_CUSTOMER, TARGET_TYPE_SUPPLIER, TARGET_TYPE_ITEM, TARGET_TYPE_INVOICE),
		route_family="control_boundary",
		unsafe_for_report_routing=True,
		description="Record mutation, workflow approval, submission, update, or deletion intent.",
	),
	DOMAIN_PREDICTION_SCORE_OR_FUTURE_CAUSE: OntologyDomainDefinition(
		name=DOMAIN_PREDICTION_SCORE_OR_FUTURE_CAUSE,
		target_types=(TARGET_TYPE_CUSTOMER, TARGET_TYPE_SUPPLIER, TARGET_TYPE_ITEM, TARGET_TYPE_REPORT),
		route_family="policy_boundary",
		unsafe_for_report_routing=True,
		description="Prediction, score, future-cause, default, or forecast intent.",
	),
	DOMAIN_LEGAL_OR_REGULATORY_ADVICE: OntologyDomainDefinition(
		name=DOMAIN_LEGAL_OR_REGULATORY_ADVICE,
		target_types=(TARGET_TYPE_CUSTOMER, TARGET_TYPE_SUPPLIER, TARGET_TYPE_INVOICE, TARGET_TYPE_PAYMENT),
		route_family="policy_boundary",
		unsafe_for_report_routing=True,
		description="Legal, regulatory, compliance, dispute, or enforcement advice intent.",
	),
	DOMAIN_UNSUPPORTED_BUSINESS_RECOMMENDATION: OntologyDomainDefinition(
		name=DOMAIN_UNSUPPORTED_BUSINESS_RECOMMENDATION,
		target_types=(TARGET_TYPE_CUSTOMER, TARGET_TYPE_SUPPLIER, TARGET_TYPE_ITEM, TARGET_TYPE_REPORT),
		route_family="policy_boundary",
		unsafe_for_report_routing=True,
		description="Unsupported business recommendation or decision request.",
	),
}


@dataclass
class ResidualSegment:
	start: int
	end: int
	text_hash: str
	status: str

	def to_payload(self) -> Dict[str, Any]:
		return {
			"start": self.start,
			"end": self.end,
			"text_hash": self.text_hash,
			"status": self.status,
		}


@dataclass
class IntentBoundaryContract:
	contract_version: str
	raw_message_hash: str
	normalized_message_hash: str
	clause_count: int
	clauses: List[Dict[str, Any]]
	erp_targets: List[Dict[str, Any]]
	visible_context_references: List[Dict[str, Any]]
	factual_lookup_intent: bool
	safe_followup_intent: bool
	decision_intent: bool
	advice_intent: bool
	business_action_intent: bool
	policy_boundary_intent: bool
	mixed_intent_detected: bool
	business_action_domain: str
	policy_domain: str
	ambiguity_status: str
	report_routing_allowed: bool
	context_reuse_allowed: bool
	model_reasoning_allowed: bool
	final_emission_allowed: bool
	required_answer_mode: str
	boundary_reason: str
	validator_status: str
	trace_redaction_status: str
	intent_proposer_role: str
	intent_proposer_status: str
	intent_proposer_confidence: float
	intent_proposer_model_name: str
	intent_proposer_output_status: str
	proposal_authority_source: str
	proposal_completeness_status: str
	clause_segmentation_status: str
	secondary_intent_audit_status: str
	residual_audit_status: str
	clause_role_confidence_status: str
	full_span_factual_authority: str
	full_span_factual_allow_reason: str
	natural_language_interpretation_required: bool
	independent_parse_guard_status: str
	lexical_authority_effect: str
	lexical_conservative_alarm: bool
	lexical_alarm_reason: str
	validator_owned_mechanical_authority_status: str
	validator_owned_mechanical_command_id: str
	clause_role_verification_required: bool
	clause_role_verifier_source: str
	clause_role_verifier_run_id: str
	clause_role_verifier_model_name: str
	clause_role_verifier_prompt_version: str
	clause_role_verifier_payload_hash: str
	clause_role_verifier_status: str
	clause_role_verifier_independence_status: str
	clause_role_verifier_authority_effect: str
	clause_role_verifier_provenance_status: str
	clause_role_verifier_payload_hash_status: str
	clause_role_verifier_attestation_status: str
	all_clause_roles_verified: bool
	proposer_verifier_agreement_status: str
	role_disagreement_policy: str
	role_verification_blocking_reason: str
	natural_language_report_authority_status: str
	validator_owned_safety_proof_required: bool
	validator_owned_safety_proof_status: str
	validator_owned_safety_proof_source: str
	validator_owned_safety_proof_version: str
	validator_owned_safety_proof_blocking_reason: str
	validator_owned_safe_route_authority_status: str
	validator_owned_safety_analyzer_id: str
	validator_owned_safety_analyzer_version: str
	validator_owned_raw_message_safety_status: str
	validator_owned_raw_message_clause_coverage_status: str
	validator_owned_raw_message_secondary_intent_status: str
	validator_owned_raw_message_mixed_intent_status: str
	validator_owned_raw_message_residual_status: str
	validator_owned_raw_message_reference_status: str
	validator_owned_safety_proof_basis: str
	validator_owned_safety_proof_attestation_status: str
	validator_owned_safety_proof_id: str
	validator_owned_safety_proof_subject_hash: str
	validator_owned_safety_proof_uniqueness_status: str
	validator_owned_safety_proof_conflict_status: str
	validator_owned_safety_proof_evidence_status: str
	validator_owned_safety_proof_evidence_semantics_status: str
	validator_owned_raw_message_analysis_required: bool
	validator_owned_raw_message_analysis_status: str
	validator_owned_raw_message_analysis_source: str
	validator_owned_raw_message_analysis_version: str
	validator_owned_raw_message_analysis_subject_hash: str
	validator_owned_raw_message_analysis_evidence_match_status: str
	validator_owned_raw_message_analysis_blocking_reason: str
	analysis_execution_required: bool
	analysis_execution_status: str
	analysis_execution_source: str
	analysis_execution_version: str
	analysis_execution_run_id: str
	analysis_execution_subject_hash: str
	analysis_execution_input_hash: str
	analysis_execution_output_hash: str
	analysis_execution_artifact_hash: str
	analysis_execution_replay_status: str
	analysis_execution_blocking_reason: str
	replayed_raw_message_safety_required: bool
	replayed_raw_message_safety_status: str
	replayed_raw_message_safety_source: str
	replayed_raw_message_safety_version: str
	replayed_raw_message_safety_config_hash: str
	replayed_raw_message_safety_subject_hash: str
	replayed_raw_message_safety_final_decision: str
	replayed_raw_message_safety_evidence_match_status: str
	replayed_raw_message_safety_blocking_reason: str
	role_verification_authority_effect: str
	semantic_backstop_authority_effect: str
	lexical_evidence_authority_effect: str
	deterministic_validator_status: str
	deterministic_validator_errors: List[str]
	semantic_backstop_status: str
	semantic_backstop_effect: str
	authority_source: str
	authority_decision: str
	authority_blocking_reason: str
	residual_text_status: str
	residual_text_segments: List[Dict[str, Any]] = field(default_factory=list)
	connector_coverage_status: str = "complete"
	pronoun_reference_status: str = "complete"
	strict_deterministic_safe_subset_status: str = "not_used"

	def to_payload(self) -> Dict[str, Any]:
		return {
			"contract_version": self.contract_version,
			"raw_message_hash": self.raw_message_hash,
			"normalized_message_hash": self.normalized_message_hash,
			"clause_count": self.clause_count,
			"clauses": self.clauses,
			"erp_targets": self.erp_targets,
			"visible_context_references": self.visible_context_references,
			"factual_lookup_intent": self.factual_lookup_intent,
			"safe_followup_intent": self.safe_followup_intent,
			"decision_intent": self.decision_intent,
			"advice_intent": self.advice_intent,
			"business_action_intent": self.business_action_intent,
			"policy_boundary_intent": self.policy_boundary_intent,
			"mixed_intent_detected": self.mixed_intent_detected,
			"business_action_domain": self.business_action_domain,
			"policy_domain": self.policy_domain,
			"ambiguity_status": self.ambiguity_status,
			"report_routing_allowed": self.report_routing_allowed,
			"context_reuse_allowed": self.context_reuse_allowed,
			"model_reasoning_allowed": self.model_reasoning_allowed,
			"final_emission_allowed": self.final_emission_allowed,
			"required_answer_mode": self.required_answer_mode,
			"boundary_reason": self.boundary_reason,
			"validator_status": self.validator_status,
			"trace_redaction_status": self.trace_redaction_status,
			"intent_proposer_role": self.intent_proposer_role,
			"intent_proposer_status": self.intent_proposer_status,
			"intent_proposer_confidence": self.intent_proposer_confidence,
			"intent_proposer_model_name": self.intent_proposer_model_name,
			"intent_proposer_output_status": self.intent_proposer_output_status,
			"proposal_authority_source": self.proposal_authority_source,
			"proposal_completeness_status": self.proposal_completeness_status,
			"clause_segmentation_status": self.clause_segmentation_status,
			"secondary_intent_audit_status": self.secondary_intent_audit_status,
			"residual_audit_status": self.residual_audit_status,
			"clause_role_confidence_status": self.clause_role_confidence_status,
			"full_span_factual_authority": self.full_span_factual_authority,
			"full_span_factual_allow_reason": self.full_span_factual_allow_reason,
			"natural_language_interpretation_required": self.natural_language_interpretation_required,
			"independent_parse_guard_status": self.independent_parse_guard_status,
			"lexical_authority_effect": self.lexical_authority_effect,
			"lexical_conservative_alarm": self.lexical_conservative_alarm,
			"lexical_alarm_reason": self.lexical_alarm_reason,
			"validator_owned_mechanical_authority_status": self.validator_owned_mechanical_authority_status,
			"validator_owned_mechanical_command_id": self.validator_owned_mechanical_command_id,
			"clause_role_verification_required": self.clause_role_verification_required,
			"clause_role_verifier_source": self.clause_role_verifier_source,
			"clause_role_verifier_run_id": self.clause_role_verifier_run_id,
			"clause_role_verifier_model_name": self.clause_role_verifier_model_name,
			"clause_role_verifier_prompt_version": self.clause_role_verifier_prompt_version,
			"clause_role_verifier_payload_hash": self.clause_role_verifier_payload_hash,
			"clause_role_verifier_status": self.clause_role_verifier_status,
			"clause_role_verifier_independence_status": self.clause_role_verifier_independence_status,
			"clause_role_verifier_authority_effect": self.clause_role_verifier_authority_effect,
			"clause_role_verifier_provenance_status": self.clause_role_verifier_provenance_status,
			"clause_role_verifier_payload_hash_status": self.clause_role_verifier_payload_hash_status,
			"clause_role_verifier_attestation_status": self.clause_role_verifier_attestation_status,
			"all_clause_roles_verified": self.all_clause_roles_verified,
			"proposer_verifier_agreement_status": self.proposer_verifier_agreement_status,
			"role_disagreement_policy": self.role_disagreement_policy,
			"role_verification_blocking_reason": self.role_verification_blocking_reason,
			"natural_language_report_authority_status": self.natural_language_report_authority_status,
			"validator_owned_safety_proof_required": self.validator_owned_safety_proof_required,
			"validator_owned_safety_proof_status": self.validator_owned_safety_proof_status,
			"validator_owned_safety_proof_source": self.validator_owned_safety_proof_source,
			"validator_owned_safety_proof_version": self.validator_owned_safety_proof_version,
			"validator_owned_safety_proof_blocking_reason": self.validator_owned_safety_proof_blocking_reason,
			"validator_owned_safe_route_authority_status": self.validator_owned_safe_route_authority_status,
			"validator_owned_safety_analyzer_id": self.validator_owned_safety_analyzer_id,
			"validator_owned_safety_analyzer_version": self.validator_owned_safety_analyzer_version,
			"validator_owned_raw_message_safety_status": self.validator_owned_raw_message_safety_status,
			"validator_owned_raw_message_clause_coverage_status": self.validator_owned_raw_message_clause_coverage_status,
			"validator_owned_raw_message_secondary_intent_status": self.validator_owned_raw_message_secondary_intent_status,
			"validator_owned_raw_message_mixed_intent_status": self.validator_owned_raw_message_mixed_intent_status,
			"validator_owned_raw_message_residual_status": self.validator_owned_raw_message_residual_status,
			"validator_owned_raw_message_reference_status": self.validator_owned_raw_message_reference_status,
			"validator_owned_safety_proof_basis": self.validator_owned_safety_proof_basis,
			"validator_owned_safety_proof_attestation_status": self.validator_owned_safety_proof_attestation_status,
			"validator_owned_safety_proof_id": self.validator_owned_safety_proof_id,
			"validator_owned_safety_proof_subject_hash": self.validator_owned_safety_proof_subject_hash,
			"validator_owned_safety_proof_uniqueness_status": self.validator_owned_safety_proof_uniqueness_status,
			"validator_owned_safety_proof_conflict_status": self.validator_owned_safety_proof_conflict_status,
			"validator_owned_safety_proof_evidence_status": self.validator_owned_safety_proof_evidence_status,
			"validator_owned_safety_proof_evidence_semantics_status": self.validator_owned_safety_proof_evidence_semantics_status,
			"validator_owned_raw_message_analysis_required": self.validator_owned_raw_message_analysis_required,
			"validator_owned_raw_message_analysis_status": self.validator_owned_raw_message_analysis_status,
			"validator_owned_raw_message_analysis_source": self.validator_owned_raw_message_analysis_source,
			"validator_owned_raw_message_analysis_version": self.validator_owned_raw_message_analysis_version,
			"validator_owned_raw_message_analysis_subject_hash": self.validator_owned_raw_message_analysis_subject_hash,
			"validator_owned_raw_message_analysis_evidence_match_status": self.validator_owned_raw_message_analysis_evidence_match_status,
			"validator_owned_raw_message_analysis_blocking_reason": self.validator_owned_raw_message_analysis_blocking_reason,
			"analysis_execution_required": self.analysis_execution_required,
			"analysis_execution_status": self.analysis_execution_status,
			"analysis_execution_source": self.analysis_execution_source,
			"analysis_execution_version": self.analysis_execution_version,
			"analysis_execution_run_id": self.analysis_execution_run_id,
			"analysis_execution_subject_hash": self.analysis_execution_subject_hash,
			"analysis_execution_input_hash": self.analysis_execution_input_hash,
			"analysis_execution_output_hash": self.analysis_execution_output_hash,
			"analysis_execution_artifact_hash": self.analysis_execution_artifact_hash,
			"analysis_execution_replay_status": self.analysis_execution_replay_status,
			"analysis_execution_blocking_reason": self.analysis_execution_blocking_reason,
			"replayed_raw_message_safety_required": self.replayed_raw_message_safety_required,
			"replayed_raw_message_safety_status": self.replayed_raw_message_safety_status,
			"replayed_raw_message_safety_source": self.replayed_raw_message_safety_source,
			"replayed_raw_message_safety_version": self.replayed_raw_message_safety_version,
			"replayed_raw_message_safety_config_hash": self.replayed_raw_message_safety_config_hash,
			"replayed_raw_message_safety_subject_hash": self.replayed_raw_message_safety_subject_hash,
			"replayed_raw_message_safety_final_decision": self.replayed_raw_message_safety_final_decision,
			"replayed_raw_message_safety_evidence_match_status": self.replayed_raw_message_safety_evidence_match_status,
			"replayed_raw_message_safety_blocking_reason": self.replayed_raw_message_safety_blocking_reason,
			"role_verification_authority_effect": self.role_verification_authority_effect,
			"semantic_backstop_authority_effect": self.semantic_backstop_authority_effect,
			"lexical_evidence_authority_effect": self.lexical_evidence_authority_effect,
			"deterministic_validator_status": self.deterministic_validator_status,
			"deterministic_validator_errors": self.deterministic_validator_errors,
			"semantic_backstop_status": self.semantic_backstop_status,
			"semantic_backstop_effect": self.semantic_backstop_effect,
			"authority_source": self.authority_source,
			"authority_decision": self.authority_decision,
			"authority_blocking_reason": self.authority_blocking_reason,
			"residual_text_status": self.residual_text_status,
			"residual_text_segments": self.residual_text_segments,
			"connector_coverage_status": self.connector_coverage_status,
			"pronoun_reference_status": self.pronoun_reference_status,
			"strict_deterministic_safe_subset_status": self.strict_deterministic_safe_subset_status,
		}


def normalize_message(raw_message: Any) -> str:
	return " ".join(str(raw_message or "").strip().lower().split())


def hash_text(value: Any) -> str:
	return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:16]


def canonical_json(value: Any) -> str:
	return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_verifier_payload(verifier_envelope: Dict[str, Any]) -> Dict[str, Any]:
	return {field_name: verifier_envelope.get(field_name) for field_name in CANONICAL_VERIFIER_PAYLOAD_FIELDS}


def canonical_verifier_payload_hash(verifier_envelope: Dict[str, Any]) -> str:
	return hash_text(canonical_json(canonical_verifier_payload(verifier_envelope)))


def verifier_attestation_hash(trusted_secret: str, computed_payload_hash: str) -> str:
	return hash_text(f"{trusted_secret}:{computed_payload_hash}")


def canonical_raw_message_safety_proof_payload(proof_entry: Dict[str, Any]) -> Dict[str, Any]:
	return {field_name: proof_entry.get(field_name) for field_name in CANONICAL_RAW_MESSAGE_SAFETY_PROOF_FIELDS}


def raw_message_safety_proof_payload_hash(proof_entry: Dict[str, Any]) -> str:
	return hash_text(canonical_json(canonical_raw_message_safety_proof_payload(proof_entry)))


def raw_message_safety_proof_attestation_hash(trusted_secret: str, computed_payload_hash: str) -> str:
	return hash_text(f"{trusted_secret}:{computed_payload_hash}")


def canonical_raw_message_analysis_payload(analysis_entry: Dict[str, Any]) -> Dict[str, Any]:
	return {field_name: analysis_entry.get(field_name) for field_name in CANONICAL_RAW_MESSAGE_ANALYSIS_FIELDS}


def raw_message_analysis_output_hash(analysis_entry: Dict[str, Any]) -> str:
	return hash_text(canonical_json(canonical_raw_message_analysis_payload(analysis_entry)))


def raw_message_analysis_input_hash(raw_message_hash: str, normalized_message_hash: str, subject_hash: str) -> str:
	return hash_text(
		canonical_json(
			{
				"raw_message_hash": raw_message_hash,
				"normalized_message_hash": normalized_message_hash,
				"raw_message_analysis_subject_hash": subject_hash,
			}
		)
	)


def canonical_raw_message_analysis_execution_payload(execution_entry: Dict[str, Any]) -> Dict[str, Any]:
	return {
		field_name: execution_entry.get(field_name)
		for field_name in CANONICAL_RAW_MESSAGE_ANALYSIS_EXECUTION_FIELDS
	}


def raw_message_analysis_execution_payload_hash(execution_entry: Dict[str, Any]) -> str:
	return hash_text(canonical_json(canonical_raw_message_analysis_execution_payload(execution_entry)))


def raw_message_analysis_execution_attestation_hash(trusted_secret: str, computed_payload_hash: str) -> str:
	return hash_text(f"{trusted_secret}:{computed_payload_hash}")


def canonical_raw_message_safety_evidence_payload(evidence: Dict[str, Any]) -> Dict[str, Any]:
	return {field_name: evidence.get(field_name) for field_name in CANONICAL_RAW_MESSAGE_SAFETY_EVIDENCE_FIELDS}


def raw_message_safety_evidence_hash(evidence: Dict[str, Any]) -> str:
	return hash_text(canonical_json(canonical_raw_message_safety_evidence_payload(evidence)))


def raw_message_safety_proof_subject_hash(raw_message_hash: str, normalized_message_hash: str) -> str:
	return hash_text(f"{raw_message_hash}:{normalized_message_hash}")


def validator_owned_safety_proof_payload(
	raw_message: Any,
	clauses: List[Dict[str, Any]],
	targets: List[Dict[str, Any]],
	references: List[Dict[str, Any]],
) -> Dict[str, Any]:
	normalized = normalize_message(raw_message)
	return {
		"proof_version": VALIDATOR_OWNED_SAFETY_PROOF_VERSION,
		"raw_message_hash": hash_text(raw_message),
		"normalized_message_hash": hash_text(normalized),
		"clause_count": len(clauses),
		"clauses": [
			{
				"clause_id": str(clause.get("clause_id") or ""),
				"index": clause.get("index"),
				"start": clause.get("start"),
				"end": clause.get("end"),
				"text_hash": hash_text(normalized[clause["start"] : clause["end"]])
				if _span_is_valid(clause.get("start"), clause.get("end"), len(normalized))
				else "",
				"clause_type": clause.get("clause_type"),
				"factual_lookup_intent": bool(clause.get("factual_lookup_intent")),
				"safe_followup_intent": bool(clause.get("safe_followup_intent")),
				"decision_intent": bool(clause.get("decision_intent")),
				"advice_intent": bool(clause.get("advice_intent")),
				"business_action_intent": bool(clause.get("business_action_intent")),
				"policy_boundary_intent": bool(clause.get("policy_boundary_intent")),
				"business_action_domain": str(clause.get("business_action_domain") or ""),
				"policy_domain": str(clause.get("policy_domain") or ""),
				"ambiguity_status": str(clause.get("ambiguity_status") or ""),
				"erp_target_ids": sorted(str(item) for item in (clause.get("erp_target_ids") or [])),
				"visible_context_reference_ids": sorted(
					str(item) for item in (clause.get("visible_context_reference_ids") or [])
				),
			}
			for clause in clauses
		],
		"targets": [
			{
				"target_id": str(target.get("target_id") or ""),
				"target_type": str(target.get("target_type") or ""),
				"value_hash": hash_text(target.get("value")),
				"schema_status": str(target.get("schema_status") or ""),
			}
			for target in targets
		],
		"references": [
			{
				"reference_id": str(reference.get("reference_id") or ""),
				"reference_type": str(reference.get("reference_type") or ""),
				"resolution_status": str(reference.get("resolution_status") or ""),
				"resolved_target_id": str(reference.get("resolved_target_id") or ""),
				"read_only_intent": bool(reference.get("read_only_intent")),
			}
			for reference in references
		],
	}


def validator_owned_safety_proof_id(
	raw_message: Any,
	clauses: List[Dict[str, Any]],
	targets: List[Dict[str, Any]],
	references: List[Dict[str, Any]],
) -> str:
	return hash_text(canonical_json(validator_owned_safety_proof_payload(raw_message, clauses, targets, references)))


def ontology_domain_values() -> Tuple[str, ...]:
	return tuple(sorted(VALID_BUSINESS_ACTION_DOMAINS))


def _is_safe_filler(segment: str) -> bool:
	return all((not char.isalnum()) for char in segment)


def detect_raw_message_unsafe_evidence(normalized_message: str) -> Dict[str, Any]:
	has_unverified_text = bool(str(normalized_message or "").strip())
	return {
		"has_unsafe_evidence": has_unverified_text,
		"raw_text_conservative_alarm": has_unverified_text,
		"alarm_reason": "validator_owned_raw_message_analysis_required" if has_unverified_text else "",
		"authority_effect": LEXICAL_AUTHORITY_EFFECT_RESTRICT_ONLY,
		"can_authorize": False,
		"evidence_model": "conservative_raw_message_analysis_required_no_route_authority",
	}


def _coerce_mapping(value: Any) -> Optional[Dict[str, Any]]:
	return value if isinstance(value, dict) else None


def _missing_fields(mapping: Dict[str, Any], required_fields: Iterable[str]) -> List[str]:
	return [field_name for field_name in required_fields if field_name not in mapping]


def _invalid_contract(
	raw_message: Any,
	errors: List[str],
	*,
	intent_proposer_role: str = "",
	intent_proposer_status: str = "",
	intent_proposer_confidence: float = 0.0,
	intent_proposer_model_name: str = "",
	intent_proposer_output_status: str = "",
	proposal_authority_source: str = "",
	proposal_completeness_status: str = "",
	clause_segmentation_status: str = "",
	secondary_intent_audit_status: str = "",
	residual_audit_status: str = "",
	clause_role_confidence_status: str = "",
	full_span_factual_authority: str = "",
	full_span_factual_allow_reason: str = "",
	natural_language_interpretation_required: bool = True,
	independent_parse_guard_status: str = "",
	lexical_authority_effect: str = LEXICAL_AUTHORITY_EFFECT_NONE,
	lexical_conservative_alarm: bool = False,
	lexical_alarm_reason: str = "",
	validator_owned_mechanical_authority_status: str = "not_validator_owned",
	validator_owned_mechanical_command_id: str = "",
	clause_role_verification_required: bool = True,
	clause_role_verifier_source: str = "",
	clause_role_verifier_run_id: str = "",
	clause_role_verifier_model_name: str = "",
	clause_role_verifier_prompt_version: str = "",
	clause_role_verifier_payload_hash: str = "",
	clause_role_verifier_status: str = "",
	clause_role_verifier_independence_status: str = "",
	clause_role_verifier_authority_effect: str = "",
	clause_role_verifier_provenance_status: str = VERIFIER_PROVENANCE_UNTRUSTED,
	clause_role_verifier_payload_hash_status: str = VERIFIER_PAYLOAD_HASH_FAILED,
	clause_role_verifier_attestation_status: str = VERIFIER_ATTESTATION_FAILED,
	all_clause_roles_verified: bool = False,
	proposer_verifier_agreement_status: str = "",
	role_disagreement_policy: str = "",
	role_verification_blocking_reason: str = "",
	natural_language_report_authority_status: str = NATURAL_LANGUAGE_REPORT_AUTHORITY_BLOCKED_WITHOUT_VERIFIER,
	validator_owned_safety_proof_required: bool = True,
	validator_owned_safety_proof_status: str = "missing",
	validator_owned_safety_proof_source: str = VALIDATOR_OWNED_SAFETY_PROOF_SOURCE,
	validator_owned_safety_proof_version: str = VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_PROOF_VERSION,
	validator_owned_safety_proof_blocking_reason: str = "validator_owned_safety_proof_missing",
	validator_owned_safe_route_authority_status: str = VALIDATOR_SAFE_ROUTE_BLOCKED_WITHOUT_PROOF,
	validator_owned_safety_analyzer_id: str = "",
	validator_owned_safety_analyzer_version: str = "",
	validator_owned_raw_message_safety_status: str = "",
	validator_owned_raw_message_clause_coverage_status: str = "",
	validator_owned_raw_message_secondary_intent_status: str = "",
	validator_owned_raw_message_mixed_intent_status: str = "",
	validator_owned_raw_message_residual_status: str = "",
	validator_owned_raw_message_reference_status: str = "",
	validator_owned_safety_proof_basis: str = "",
	validator_owned_safety_proof_attestation_status: str = SAFETY_PROOF_ATTESTATION_FAILED,
	validator_owned_safety_proof_id: str = "",
	validator_owned_safety_proof_subject_hash: str = "",
	validator_owned_safety_proof_uniqueness_status: str = "",
	validator_owned_safety_proof_conflict_status: str = "",
	validator_owned_safety_proof_evidence_status: str = "",
	validator_owned_safety_proof_evidence_semantics_status: str = "",
	validator_owned_raw_message_analysis_required: bool = True,
	validator_owned_raw_message_analysis_status: str = "missing",
	validator_owned_raw_message_analysis_source: str = VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_SOURCE,
	validator_owned_raw_message_analysis_version: str = VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_VERSION,
	validator_owned_raw_message_analysis_subject_hash: str = "",
	validator_owned_raw_message_analysis_evidence_match_status: str = "",
	validator_owned_raw_message_analysis_blocking_reason: str = "validator_owned_raw_message_analysis_missing",
	analysis_execution_required: bool = True,
	analysis_execution_status: str = "missing",
	analysis_execution_source: str = VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_SOURCE,
	analysis_execution_version: str = VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_VERSION,
	analysis_execution_run_id: str = "",
	analysis_execution_subject_hash: str = "",
	analysis_execution_input_hash: str = "",
	analysis_execution_output_hash: str = "",
	analysis_execution_artifact_hash: str = "",
	analysis_execution_replay_status: str = "",
	analysis_execution_blocking_reason: str = "analysis_execution_missing",
	replayed_raw_message_safety_required: bool = True,
	replayed_raw_message_safety_status: str = "missing",
	replayed_raw_message_safety_source: str = VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_SOURCE,
	replayed_raw_message_safety_version: str = VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_VERSION,
	replayed_raw_message_safety_config_hash: str = "",
	replayed_raw_message_safety_subject_hash: str = "",
	replayed_raw_message_safety_final_decision: str = "blocked",
	replayed_raw_message_safety_evidence_match_status: str = "",
	replayed_raw_message_safety_blocking_reason: str = "validator_owned_replay_missing",
	role_verification_authority_effect: str = ROLE_VERIFICATION_AUTHORITY_EFFECT_CONSISTENCY_ONLY,
	semantic_backstop_authority_effect: str = SEMANTIC_BACKSTOP_AUTHORITY_EFFECT_RESTRICT_ONLY,
	lexical_evidence_authority_effect: str = LEXICAL_EVIDENCE_AUTHORITY_EFFECT_RESTRICT_ONLY,
	semantic_backstop_status: str = SEMANTIC_BACKSTOP_MISSING,
	semantic_backstop_effect: str = "none",
	residual_segments: Optional[List[ResidualSegment]] = None,
	trace_redaction_status: str = "unknown",
	pronoun_reference_status: str = "unknown",
	connector_coverage_status: str = "unknown",
) -> IntentBoundaryContract:
	normalized = normalize_message(raw_message)
	return IntentBoundaryContract(
		contract_version=CONTRACT_VERSION,
		raw_message_hash=hash_text(raw_message),
		normalized_message_hash=hash_text(normalized),
		clause_count=0,
		clauses=[],
		erp_targets=[],
		visible_context_references=[],
		factual_lookup_intent=False,
		safe_followup_intent=False,
		decision_intent=False,
		advice_intent=False,
		business_action_intent=False,
		policy_boundary_intent=False,
		mixed_intent_detected=False,
		business_action_domain=DOMAIN_NONE,
		policy_domain=DOMAIN_NONE,
		ambiguity_status="invalid",
		report_routing_allowed=False,
		context_reuse_allowed=False,
		model_reasoning_allowed=False,
		final_emission_allowed=False,
		required_answer_mode=ANSWER_MODE_CLARIFICATION,
		boundary_reason="invalid_intent_boundary_contract",
		validator_status=DETERMINISTIC_VALIDATOR_INVALID,
		trace_redaction_status=trace_redaction_status,
		intent_proposer_role=intent_proposer_role,
		intent_proposer_status=intent_proposer_status,
		intent_proposer_confidence=intent_proposer_confidence,
		intent_proposer_model_name=intent_proposer_model_name,
		intent_proposer_output_status=intent_proposer_output_status,
		proposal_authority_source=proposal_authority_source,
		proposal_completeness_status=proposal_completeness_status,
		clause_segmentation_status=clause_segmentation_status,
		secondary_intent_audit_status=secondary_intent_audit_status,
		residual_audit_status=residual_audit_status,
		clause_role_confidence_status=clause_role_confidence_status,
		full_span_factual_authority=full_span_factual_authority,
		full_span_factual_allow_reason=full_span_factual_allow_reason,
		natural_language_interpretation_required=natural_language_interpretation_required,
		independent_parse_guard_status=independent_parse_guard_status,
		lexical_authority_effect=lexical_authority_effect,
		lexical_conservative_alarm=lexical_conservative_alarm,
		lexical_alarm_reason=lexical_alarm_reason,
		validator_owned_mechanical_authority_status=validator_owned_mechanical_authority_status,
		validator_owned_mechanical_command_id=validator_owned_mechanical_command_id,
		clause_role_verification_required=clause_role_verification_required,
		clause_role_verifier_source=clause_role_verifier_source,
		clause_role_verifier_run_id=clause_role_verifier_run_id,
		clause_role_verifier_model_name=clause_role_verifier_model_name,
		clause_role_verifier_prompt_version=clause_role_verifier_prompt_version,
		clause_role_verifier_payload_hash=clause_role_verifier_payload_hash,
		clause_role_verifier_status=clause_role_verifier_status,
		clause_role_verifier_independence_status=clause_role_verifier_independence_status,
		clause_role_verifier_authority_effect=clause_role_verifier_authority_effect,
		clause_role_verifier_provenance_status=clause_role_verifier_provenance_status,
		clause_role_verifier_payload_hash_status=clause_role_verifier_payload_hash_status,
		clause_role_verifier_attestation_status=clause_role_verifier_attestation_status,
		all_clause_roles_verified=all_clause_roles_verified,
		proposer_verifier_agreement_status=proposer_verifier_agreement_status,
		role_disagreement_policy=role_disagreement_policy,
		role_verification_blocking_reason=role_verification_blocking_reason,
		natural_language_report_authority_status=natural_language_report_authority_status,
		validator_owned_safety_proof_required=validator_owned_safety_proof_required,
		validator_owned_safety_proof_status=validator_owned_safety_proof_status,
		validator_owned_safety_proof_source=validator_owned_safety_proof_source,
		validator_owned_safety_proof_version=validator_owned_safety_proof_version,
		validator_owned_safety_proof_blocking_reason=validator_owned_safety_proof_blocking_reason,
		validator_owned_safe_route_authority_status=validator_owned_safe_route_authority_status,
		validator_owned_safety_analyzer_id=validator_owned_safety_analyzer_id,
		validator_owned_safety_analyzer_version=validator_owned_safety_analyzer_version,
		validator_owned_raw_message_safety_status=validator_owned_raw_message_safety_status,
		validator_owned_raw_message_clause_coverage_status=validator_owned_raw_message_clause_coverage_status,
		validator_owned_raw_message_secondary_intent_status=validator_owned_raw_message_secondary_intent_status,
		validator_owned_raw_message_mixed_intent_status=validator_owned_raw_message_mixed_intent_status,
		validator_owned_raw_message_residual_status=validator_owned_raw_message_residual_status,
		validator_owned_raw_message_reference_status=validator_owned_raw_message_reference_status,
		validator_owned_safety_proof_basis=validator_owned_safety_proof_basis,
		validator_owned_safety_proof_attestation_status=validator_owned_safety_proof_attestation_status,
		validator_owned_safety_proof_id=validator_owned_safety_proof_id,
		validator_owned_safety_proof_subject_hash=validator_owned_safety_proof_subject_hash,
		validator_owned_safety_proof_uniqueness_status=validator_owned_safety_proof_uniqueness_status,
		validator_owned_safety_proof_conflict_status=validator_owned_safety_proof_conflict_status,
		validator_owned_safety_proof_evidence_status=validator_owned_safety_proof_evidence_status,
		validator_owned_safety_proof_evidence_semantics_status=validator_owned_safety_proof_evidence_semantics_status,
		validator_owned_raw_message_analysis_required=validator_owned_raw_message_analysis_required,
		validator_owned_raw_message_analysis_status=validator_owned_raw_message_analysis_status,
		validator_owned_raw_message_analysis_source=validator_owned_raw_message_analysis_source,
		validator_owned_raw_message_analysis_version=validator_owned_raw_message_analysis_version,
		validator_owned_raw_message_analysis_subject_hash=validator_owned_raw_message_analysis_subject_hash,
		validator_owned_raw_message_analysis_evidence_match_status=validator_owned_raw_message_analysis_evidence_match_status,
		validator_owned_raw_message_analysis_blocking_reason=validator_owned_raw_message_analysis_blocking_reason,
		analysis_execution_required=analysis_execution_required,
		analysis_execution_status=analysis_execution_status,
		analysis_execution_source=analysis_execution_source,
		analysis_execution_version=analysis_execution_version,
		analysis_execution_run_id=analysis_execution_run_id,
		analysis_execution_subject_hash=analysis_execution_subject_hash,
		analysis_execution_input_hash=analysis_execution_input_hash,
		analysis_execution_output_hash=analysis_execution_output_hash,
		analysis_execution_artifact_hash=analysis_execution_artifact_hash,
		analysis_execution_replay_status=analysis_execution_replay_status,
		analysis_execution_blocking_reason=analysis_execution_blocking_reason,
		replayed_raw_message_safety_required=replayed_raw_message_safety_required,
		replayed_raw_message_safety_status=replayed_raw_message_safety_status,
		replayed_raw_message_safety_source=replayed_raw_message_safety_source,
		replayed_raw_message_safety_version=replayed_raw_message_safety_version,
		replayed_raw_message_safety_config_hash=replayed_raw_message_safety_config_hash,
		replayed_raw_message_safety_subject_hash=replayed_raw_message_safety_subject_hash,
		replayed_raw_message_safety_final_decision=replayed_raw_message_safety_final_decision,
		replayed_raw_message_safety_evidence_match_status=replayed_raw_message_safety_evidence_match_status,
		replayed_raw_message_safety_blocking_reason=replayed_raw_message_safety_blocking_reason,
		role_verification_authority_effect=role_verification_authority_effect,
		semantic_backstop_authority_effect=semantic_backstop_authority_effect,
		lexical_evidence_authority_effect=lexical_evidence_authority_effect,
		deterministic_validator_status=DETERMINISTIC_VALIDATOR_INVALID,
		deterministic_validator_errors=errors,
		semantic_backstop_status=semantic_backstop_status,
		semantic_backstop_effect=semantic_backstop_effect,
		authority_source=AUTHORITY_SOURCE_DETERMINISTIC_VALIDATOR,
		authority_decision=AUTHORITY_DECISION_BLOCK,
		authority_blocking_reason=";".join(errors),
		residual_text_status="unresolved" if residual_segments else "unknown",
		residual_text_segments=[segment.to_payload() for segment in residual_segments or []],
		connector_coverage_status=connector_coverage_status,
		pronoun_reference_status=pronoun_reference_status,
	)


def _span_is_valid(start: Any, end: Any, message_length: int) -> bool:
	return isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= message_length


def _compute_residual_segments(normalized_message: str, clauses: List[Dict[str, Any]]) -> List[ResidualSegment]:
	covered = [False] * len(normalized_message)
	for clause in clauses:
		start = clause["start"]
		end = clause["end"]
		for index in range(start, end):
			covered[index] = True
	segments: List[ResidualSegment] = []
	index = 0
	while index < len(normalized_message):
		if covered[index]:
			index += 1
			continue
		start = index
		while index < len(normalized_message) and not covered[index]:
			index += 1
		residual_text = normalized_message[start:index]
		status = "safe_filler" if _is_safe_filler(residual_text) else "unresolved"
		if status != "safe_filler":
			segments.append(
				ResidualSegment(
					start=start,
					end=index,
					text_hash=hash_text(residual_text),
					status=status,
				)
			)
	return segments


def _redact_clause(clause: Dict[str, Any]) -> Dict[str, Any]:
	text = str(clause.get("text") or "")
	return {
		"clause_id": clause["clause_id"],
		"index": clause["index"],
		"start": clause["start"],
		"end": clause["end"],
		"text_hash": hash_text(text),
		"clause_type": clause["clause_type"],
		"erp_target_ids": list(clause.get("erp_target_ids") or []),
		"visible_context_reference_ids": list(clause.get("visible_context_reference_ids") or []),
		"factual_lookup_intent": bool(clause["factual_lookup_intent"]),
		"safe_followup_intent": bool(clause["safe_followup_intent"]),
		"decision_intent": bool(clause["decision_intent"]),
		"advice_intent": bool(clause["advice_intent"]),
		"business_action_intent": bool(clause["business_action_intent"]),
		"policy_boundary_intent": bool(clause["policy_boundary_intent"]),
		"business_action_domain": clause["business_action_domain"],
		"policy_domain": clause["policy_domain"],
		"ambiguity_status": clause["ambiguity_status"],
		"verified_clause_type": str(clause.get("verified_clause_type") or ""),
		"verified_factual_lookup_intent": bool(clause.get("verified_factual_lookup_intent")),
		"verified_safe_followup_intent": bool(clause.get("verified_safe_followup_intent")),
		"verified_decision_intent": bool(clause.get("verified_decision_intent")),
		"verified_advice_intent": bool(clause.get("verified_advice_intent")),
		"verified_business_action_intent": bool(clause.get("verified_business_action_intent")),
		"verified_policy_boundary_intent": bool(clause.get("verified_policy_boundary_intent")),
		"verified_business_action_domain": str(clause.get("verified_business_action_domain") or ""),
		"verified_policy_domain": str(clause.get("verified_policy_domain") or ""),
		"verification_status": str(clause.get("verification_status") or ""),
		"verification_confidence": float(clause.get("verification_confidence") or 0.0),
		"verification_blocking_reason": str(clause.get("verification_blocking_reason") or ""),
	}


def _redact_target(target: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"target_id": target["target_id"],
		"target_type": target["target_type"],
		"value_hash": hash_text(target.get("value")),
		"schema_status": target["schema_status"],
		"trace_redaction_status": TRACE_REDACTION_SAFE,
	}


def _reference_payload(reference: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"reference_id": reference["reference_id"],
		"reference_type": reference["reference_type"],
		"resolution_status": reference["resolution_status"],
		"resolved_target_id": str(reference.get("resolved_target_id") or ""),
		"read_only_intent": bool(reference["read_only_intent"]),
	}


def _validate_targets(targets: Any, errors: List[str]) -> List[Dict[str, Any]]:
	if not isinstance(targets, list):
		errors.append("erp_targets_not_list")
		return []
	valid_targets: List[Dict[str, Any]] = []
	seen_ids = set()
	for target in targets:
		if not isinstance(target, dict):
			errors.append("erp_target_not_object")
			continue
		missing = _missing_fields(target, REQUIRED_TARGET_FIELDS)
		if missing:
			errors.append("erp_target_missing_fields")
			continue
		if target["target_id"] in seen_ids:
			errors.append("duplicate_erp_target_id")
		seen_ids.add(target["target_id"])
		if target["target_type"] not in VALID_TARGET_TYPES:
			errors.append("invalid_erp_target_type")
		if target["schema_status"] != "valid":
			errors.append("invalid_erp_target_schema_status")
		valid_targets.append(target)
	return valid_targets


def _validate_references(references: Any, target_ids: set, errors: List[str]) -> List[Dict[str, Any]]:
	if not isinstance(references, list):
		errors.append("visible_context_references_not_list")
		return []
	valid_references: List[Dict[str, Any]] = []
	for reference in references:
		if not isinstance(reference, dict):
			errors.append("visible_context_reference_not_object")
			continue
		missing = _missing_fields(reference, REQUIRED_REFERENCE_FIELDS)
		if missing:
			errors.append("visible_context_reference_missing_fields")
			continue
		if reference["reference_type"] not in VALID_REFERENCE_TYPES:
			errors.append("invalid_visible_context_reference_type")
		if reference["resolution_status"] not in VALID_REFERENCE_STATUSES:
			errors.append("invalid_visible_context_resolution_status")
		if reference["resolution_status"] == REFERENCE_UNRESOLVED:
			errors.append("unresolved_visible_context_reference")
		if reference["resolution_status"] == REFERENCE_RESOLVED and reference.get("resolved_target_id") not in target_ids:
			errors.append("visible_context_reference_target_missing")
		if reference["resolution_status"] == REFERENCE_RESOLVED and not reference["read_only_intent"]:
			errors.append("visible_context_reference_not_read_only")
		valid_references.append(reference)
	return valid_references


def _validate_clauses(
	clauses: Any,
	normalized_message: str,
	target_ids: set,
	reference_ids: set,
	errors: List[str],
) -> List[Dict[str, Any]]:
	if not isinstance(clauses, list):
		errors.append("clauses_not_list")
		return []
	valid_clauses: List[Dict[str, Any]] = []
	last_start = -1
	for expected_index, clause in enumerate(clauses):
		if not isinstance(clause, dict):
			errors.append("clause_not_object")
			continue
		missing = _missing_fields(clause, REQUIRED_CLAUSE_FIELDS)
		if missing:
			errors.append("clause_missing_fields")
			continue
		if clause["index"] != expected_index:
			errors.append("clause_index_order_mismatch")
		if not _span_is_valid(clause["start"], clause["end"], len(normalized_message)):
			errors.append("clause_span_invalid")
			continue
		if clause["start"] < last_start:
			errors.append("clause_order_not_preserved")
		last_start = clause["start"]
		span_text = normalized_message[clause["start"] : clause["end"]]
		if normalize_message(clause.get("text")) != span_text:
			errors.append("clause_text_span_mismatch")
		if clause["clause_type"] not in VALID_CLAUSE_TYPES:
			errors.append("invalid_clause_type")
		if clause["business_action_domain"] not in VALID_BUSINESS_ACTION_DOMAINS:
			errors.append("invalid_business_action_domain")
		if clause["policy_domain"] not in VALID_BUSINESS_ACTION_DOMAINS:
			errors.append("invalid_policy_domain")
		for target_id in clause.get("erp_target_ids") or []:
			if target_id not in target_ids:
				errors.append("clause_target_missing")
		for reference_id in clause.get("visible_context_reference_ids") or []:
			if reference_id not in reference_ids:
				errors.append("clause_reference_missing")
		if clause["clause_type"] == CLAUSE_TYPE_FACTUAL_LOOKUP and clause["business_action_intent"]:
			errors.append("contradictory_factual_clause_business_action")
		if clause["clause_type"] == CLAUSE_TYPE_FACTUAL_LOOKUP and clause["policy_boundary_intent"]:
			errors.append("contradictory_factual_clause_policy_boundary")
		if clause["business_action_domain"] != DOMAIN_NONE and not clause["business_action_intent"]:
			errors.append("domain_without_business_action_intent")
		if clause["decision_intent"] and clause["clause_type"] == CLAUSE_TYPE_FACTUAL_LOOKUP:
			errors.append("decision_intent_in_factual_clause")
		valid_clauses.append(clause)
	return valid_clauses


def _proposal_metadata_errors(proposal: Dict[str, Any]) -> List[str]:
	errors: List[str] = []
	if proposal.get("intent_proposer_role") != PROPOSER_ROLE_LIGHTWEIGHT:
		errors.append("invalid_intent_proposer_role")
	if proposal.get("intent_proposer_status") != PROPOSER_STATUS_COMPLETE:
		errors.append("intent_proposer_status_not_complete")
	try:
		confidence = float(proposal.get("intent_proposer_confidence"))
	except (TypeError, ValueError):
		confidence = -1.0
	if confidence < MIN_PROPOSER_CONFIDENCE:
		errors.append("intent_proposer_confidence_too_low")
	if not str(proposal.get("intent_proposer_model_name") or "").strip():
		errors.append("intent_proposer_model_name_missing")
	if proposal.get("intent_proposer_output_status") != PROPOSER_OUTPUT_VALID:
		errors.append("intent_proposer_output_status_not_valid")
	if proposal.get("trace_redaction_status") != TRACE_REDACTION_SAFE:
		errors.append("trace_redaction_status_not_safe")
	model_name = str(proposal.get("intent_proposer_model_name") or "").strip()
	authority_source = str(proposal.get("proposal_authority_source") or "").strip()
	if model_name in FORBIDDEN_LEXICAL_PROPOSER_IDENTIFIERS or authority_source in FORBIDDEN_LEXICAL_PROPOSER_IDENTIFIERS:
		errors.append("lexical_classifier_cannot_authorize")
	if authority_source != PROPOSAL_SOURCE_LIGHTWEIGHT_MODEL:
		errors.append("proposal_authority_source_not_trusted")
	return errors


def _is_full_span_factual_clause(clauses: List[Dict[str, Any]], normalized_message: str) -> bool:
	return bool(
		len(clauses) == 1
		and clauses[0]["clause_type"] == CLAUSE_TYPE_FACTUAL_LOOKUP
		and clauses[0]["factual_lookup_intent"] is True
		and clauses[0]["start"] == 0
		and clauses[0]["end"] == len(normalized_message)
	)


def _validator_owned_mechanical_status(command_id: Any) -> Tuple[str, str]:
	if not isinstance(command_id, str) or not command_id.strip():
		return "not_requested", ""
	command_id = command_id.strip()
	registry_entry = VALIDATOR_OWNED_MECHANICAL_COMMAND_REGISTRY.get(command_id)
	if not registry_entry or registry_entry.get("registry_status") != "approved":
		return "not_validator_owned", command_id
	return "validator_owned_approved", command_id


def _trusted_verifier_registry(
	registry: Optional[Dict[str, Dict[str, Any]]],
) -> Dict[str, Dict[str, Any]]:
	return registry if registry is not None else VALIDATOR_OWNED_TRUSTED_VERIFIER_REGISTRY


def _trusted_safety_proof_registry(
	registry: Optional[Dict[str, Dict[str, Any]]],
) -> Dict[str, Dict[str, Any]]:
	_ = registry
	return VALIDATOR_OWNED_SAFETY_PROOF_REGISTRY


def _trusted_raw_message_analysis_registry() -> Dict[str, Dict[str, Any]]:
	return VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_REGISTRY


def _trusted_raw_message_analysis_execution_registry() -> Dict[str, Dict[str, Any]]:
	return VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_REGISTRY


def _registry_values(entry: Dict[str, Any], field_name: str) -> set:
	value = entry.get(field_name)
	if isinstance(value, str):
		return {value}
	if isinstance(value, (list, tuple, set)):
		return {str(item) for item in value}
	return set()


def _evidence_contains_raw_business_text(value: Any) -> bool:
	if isinstance(value, dict):
		return any(_evidence_contains_raw_business_text(item) for item in value.values())
	if isinstance(value, (list, tuple, set)):
		return any(_evidence_contains_raw_business_text(item) for item in value)
	if isinstance(value, str):
		normalized_value = value.lower()
		return "ec7h-" in normalized_value or "item sales" in normalized_value
	return False


def _validate_raw_message_safety_evidence_objects(
	proof_entry: Dict[str, Any],
	analyzer_id: str,
	analyzer_version: str,
) -> Tuple[List[str], str]:
	errors: List[str] = []
	semantic_status = "passed"
	for proof_field, requirement in RAW_MESSAGE_SAFETY_EVIDENCE_REQUIREMENTS.items():
		evidence = proof_entry.get(proof_field)
		if not isinstance(evidence, dict):
			errors.append("validator_owned_safety_proof_evidence_object_missing")
			semantic_status = "missing"
			continue
		if set(evidence.keys()) - set(REQUIRED_RAW_MESSAGE_SAFETY_EVIDENCE_FIELDS):
			errors.append("validator_owned_safety_proof_evidence_object_malformed")
			semantic_status = "malformed"
		if _missing_fields(evidence, REQUIRED_RAW_MESSAGE_SAFETY_EVIDENCE_FIELDS):
			errors.append("validator_owned_safety_proof_evidence_object_missing_fields")
			semantic_status = "malformed"
			continue
		if evidence.get("evidence_type") != requirement["evidence_type"]:
			errors.append("validator_owned_safety_proof_evidence_type_mismatch")
			semantic_status = "contradictory"
		evidence_status = str(evidence.get("evidence_status") or "")
		if evidence_status in UNSAFE_EVIDENCE_STATUSES:
			errors.append("validator_owned_safety_proof_evidence_unsafe_or_ambiguous")
			semantic_status = "unsafe_or_ambiguous"
		if evidence_status != requirement["evidence_status"]:
			errors.append("validator_owned_safety_proof_evidence_status_mismatch")
			semantic_status = "contradictory"
		proof_status_field = str(requirement.get("proof_status_field") or "")
		if proof_status_field and evidence_status != str(proof_entry.get(proof_status_field) or ""):
			errors.append("validator_owned_safety_proof_evidence_contradicts_proof_status")
			semantic_status = "contradictory"
		if evidence.get("evidence_basis") != RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE:
			errors.append("validator_owned_safety_proof_evidence_basis_not_non_derivative")
			semantic_status = "derived"
		if evidence.get("source_analyzer_id") != analyzer_id or evidence.get("source_analyzer_version") != analyzer_version:
			errors.append("validator_owned_safety_proof_evidence_source_mismatch")
			semantic_status = "contradictory"
		for derivation_field in (
			"derived_from_proposer_roles",
			"derived_from_verifier_roles",
			"derived_from_semantic_safe_output",
			"derived_from_lexical_phrase_authority",
		):
			if evidence.get(derivation_field) is True:
				errors.append(f"validator_owned_safety_proof_evidence_{derivation_field}")
				semantic_status = "derived"
		if evidence.get("redaction_status") != TRACE_REDACTION_SAFE:
			errors.append("validator_owned_safety_proof_evidence_redaction_not_safe")
			semantic_status = "redaction_failed"
		if _evidence_contains_raw_business_text(evidence):
			errors.append("validator_owned_safety_proof_evidence_raw_business_text")
			semantic_status = "redaction_failed"
		computed_evidence_hash = raw_message_safety_evidence_hash(evidence)
		if evidence.get("evidence_hash") != computed_evidence_hash:
			errors.append("validator_owned_safety_proof_evidence_hash_mismatch")
			semantic_status = "tampered"
		proof_hash_field = RAW_MESSAGE_SAFETY_EVIDENCE_HASH_FIELDS.get(proof_field)
		if proof_hash_field and proof_entry.get(proof_hash_field) != evidence.get("evidence_hash"):
			errors.append("validator_owned_safety_proof_evidence_hash_field_mismatch")
			semantic_status = "contradictory"
	return errors, semantic_status


def _proof_evidence_hashes(proof_entry: Dict[str, Any]) -> Dict[str, str]:
	return {
		"raw_message_clause_coverage_evidence_hash": str(
			(proof_entry.get("raw_message_clause_coverage_evidence") or {}).get("evidence_hash") or ""
		),
		"raw_message_secondary_intent_evidence_hash": str(
			(proof_entry.get("raw_message_secondary_intent_evidence") or {}).get("evidence_hash") or ""
		),
		"raw_message_mixed_intent_evidence_hash": str(
			(proof_entry.get("raw_message_mixed_intent_evidence") or {}).get("evidence_hash") or ""
		),
		"raw_message_residual_evidence_hash": str(
			(proof_entry.get("raw_message_residual_evidence") or {}).get("evidence_hash") or ""
		),
		"raw_message_connector_evidence_hash": str(
			(proof_entry.get("raw_message_connector_evidence") or {}).get("evidence_hash") or ""
		),
		"raw_message_reference_evidence_hash": str(
			(proof_entry.get("raw_message_reference_evidence") or {}).get("evidence_hash") or ""
		),
		"raw_message_unsafe_ambiguity_evidence_hash": str(
			(proof_entry.get("raw_message_unsafe_ambiguity_evidence") or {}).get("evidence_hash") or ""
		),
	}


def _validate_validator_owned_raw_message_analysis(
	proof_entry: Dict[str, Any],
	normalized_message: str,
	raw_hash: str,
	normalized_hash: str,
	subject_hash: str,
	residual_segments: List[ResidualSegment],
	connector_coverage_status: str,
	pronoun_reference_status: str,
) -> Tuple[List[str], Dict[str, str]]:
	errors: List[str] = []
	metadata = {
		"validator_owned_raw_message_analysis_required": True,
		"validator_owned_raw_message_analysis_status": "missing",
		"validator_owned_raw_message_analysis_source": VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_SOURCE,
		"validator_owned_raw_message_analysis_version": VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_VERSION,
		"validator_owned_raw_message_analysis_subject_hash": subject_hash,
		"validator_owned_raw_message_analysis_evidence_match_status": "unknown",
		"validator_owned_raw_message_analysis_blocking_reason": "",
	}
	analysis_matches: List[Dict[str, Any]] = []
	for analysis in _trusted_raw_message_analysis_registry().values():
		if not isinstance(analysis, dict):
			continue
		if analysis.get("registry_status") != "approved":
			continue
		if analysis.get("raw_message_hash") == raw_hash and analysis.get("normalized_message_hash") == normalized_hash:
			analysis_matches.append(analysis)
	if not analysis_matches:
		errors.append("validator_owned_raw_message_analysis_missing")
		metadata["validator_owned_raw_message_analysis_evidence_match_status"] = "missing"
	elif len(analysis_matches) > 1:
		errors.append("validator_owned_raw_message_analysis_conflict_detected")
		metadata["validator_owned_raw_message_analysis_status"] = "conflict"
		metadata["validator_owned_raw_message_analysis_evidence_match_status"] = "conflict"
	else:
		analysis = analysis_matches[0]
		if _missing_fields(analysis, REQUIRED_RAW_MESSAGE_ANALYSIS_FIELDS):
			errors.append("validator_owned_raw_message_analysis_missing_fields")
		metadata["validator_owned_raw_message_analysis_status"] = str(analysis.get("analysis_status") or "")
		metadata["validator_owned_raw_message_analysis_subject_hash"] = str(
			analysis.get("raw_message_analysis_subject_hash") or subject_hash
		)
		if analysis.get("raw_message_analysis_subject_hash") != subject_hash:
			errors.append("validator_owned_raw_message_analysis_subject_mismatch")
		if analysis.get("analysis_source") != VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_SOURCE:
			errors.append("validator_owned_raw_message_analysis_source_invalid")
		if analysis.get("analysis_version") != VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_VERSION:
			errors.append("validator_owned_raw_message_analysis_version_invalid")
		if analysis.get("analysis_status") != "safe":
			errors.append("validator_owned_raw_message_analysis_not_safe")
		status_pairs = (
			("raw_message_clause_coverage_status", "validator_owned_raw_message_analysis_clause_coverage_contradicts_proof"),
			("raw_message_secondary_intent_status", "validator_owned_raw_message_analysis_secondary_intent_contradicts_proof"),
			("raw_message_mixed_intent_status", "validator_owned_raw_message_analysis_mixed_intent_contradicts_proof"),
			("raw_message_residual_status", "validator_owned_raw_message_analysis_residual_contradicts_proof"),
			("raw_message_reference_status", "validator_owned_raw_message_analysis_reference_contradicts_proof"),
		)
		for field_name, error_name in status_pairs:
			if analysis.get(field_name) != proof_entry.get(field_name):
				errors.append(error_name)
		if analysis.get("raw_message_connector_status") != "accounted":
			errors.append("validator_owned_raw_message_analysis_connector_contradicts_proof")
		if analysis.get("raw_message_unsafe_ambiguity_status") != "none":
			errors.append("validator_owned_raw_message_analysis_unsafe_ambiguity_contradicts_proof")
		if analysis.get("validator_safety_analyzer_id") != proof_entry.get("validator_safety_analyzer_id"):
			errors.append("validator_owned_raw_message_analysis_analyzer_id_mismatch")
		if analysis.get("validator_safety_analyzer_version") != proof_entry.get("validator_safety_analyzer_version"):
			errors.append("validator_owned_raw_message_analysis_analyzer_version_mismatch")
		if analysis.get("analysis_basis") != RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE:
			errors.append("validator_owned_raw_message_analysis_basis_not_non_derivative")
		for derivation_field in (
			"derived_from_proposer_roles",
			"derived_from_verifier_roles",
			"derived_from_semantic_safe_output",
			"derived_from_lexical_phrase_authority",
		):
			if analysis.get(derivation_field) is True:
				errors.append(f"validator_owned_raw_message_analysis_{derivation_field}")
		if analysis.get("trace_redaction_status") != TRACE_REDACTION_SAFE or _evidence_contains_raw_business_text(analysis):
			errors.append("validator_owned_raw_message_analysis_redaction_not_safe")
		proof_hashes = _proof_evidence_hashes(proof_entry)
		for field_name, proof_hash in proof_hashes.items():
			if not proof_hash or analysis.get(field_name) != proof_hash:
				errors.append("validator_owned_raw_message_analysis_evidence_hash_mismatch")
				break
		if "validator_owned_raw_message_analysis_evidence_hash_mismatch" in errors:
			metadata["validator_owned_raw_message_analysis_evidence_match_status"] = "mismatch"
		else:
			metadata["validator_owned_raw_message_analysis_evidence_match_status"] = "matched"
		execution_errors, execution_metadata = _validate_raw_message_analysis_execution(
			analysis,
			raw_hash,
			normalized_hash,
			subject_hash,
			VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY.get(
				str(analysis.get("validator_safety_analyzer_id") or "")
			),
		)
		errors.extend(execution_errors)
		metadata.update(execution_metadata)
		replay_result = _replay_raw_message_safety(
			normalized_message,
			subject_hash,
			residual_segments,
			connector_coverage_status,
			pronoun_reference_status,
			analysis,
			VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY.get(
				str(analysis.get("validator_safety_analyzer_id") or "")
			),
		)
		replay_errors, replay_metadata = _validate_replayed_raw_message_safety(
			replay_result,
			proof_entry,
			analysis,
		)
		errors.extend(replay_errors)
		metadata.update(replay_metadata)
	if errors:
		metadata["validator_owned_raw_message_analysis_blocking_reason"] = ";".join(errors)
	elif metadata["validator_owned_raw_message_analysis_status"] == "safe":
		metadata["validator_owned_raw_message_analysis_blocking_reason"] = ""
	return errors, metadata


def _validate_raw_message_analysis_execution(
	analysis: Dict[str, Any],
	raw_hash: str,
	normalized_hash: str,
	subject_hash: str,
	analyzer_entry: Optional[Dict[str, Any]],
) -> Tuple[List[str], Dict[str, str]]:
	errors: List[str] = []
	expected_input_hash = raw_message_analysis_input_hash(raw_hash, normalized_hash, subject_hash)
	expected_output_hash = raw_message_analysis_output_hash(analysis)
	metadata = {
		"analysis_execution_required": True,
		"analysis_execution_status": "missing",
		"analysis_execution_source": VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_SOURCE,
		"analysis_execution_version": VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_VERSION,
		"analysis_execution_run_id": "",
		"analysis_execution_subject_hash": subject_hash,
		"analysis_execution_input_hash": expected_input_hash,
		"analysis_execution_output_hash": expected_output_hash,
		"analysis_execution_artifact_hash": "",
		"analysis_execution_replay_status": "",
		"analysis_execution_blocking_reason": "",
	}
	matches: List[Dict[str, Any]] = []
	for execution in _trusted_raw_message_analysis_execution_registry().values():
		if not isinstance(execution, dict):
			continue
		if execution.get("registry_status") != "approved":
			continue
		if execution.get("raw_message_hash") == raw_hash and execution.get("normalized_message_hash") == normalized_hash:
			matches.append(execution)
	if not matches:
		errors.append("analysis_execution_missing")
	elif len(matches) > 1:
		errors.append("analysis_execution_conflict_detected")
		metadata["analysis_execution_status"] = "conflict"
	else:
		execution = matches[0]
		metadata.update(
			{
				"analysis_execution_status": str(execution.get("execution_status") or ""),
				"analysis_execution_source": str(execution.get("execution_source") or ""),
				"analysis_execution_version": str(execution.get("execution_version") or ""),
				"analysis_execution_run_id": str(execution.get("run_id") or ""),
				"analysis_execution_input_hash": str(execution.get("input_hash") or ""),
				"analysis_execution_output_hash": str(execution.get("output_hash") or ""),
				"analysis_execution_artifact_hash": str(execution.get("artifact_hash") or ""),
				"analysis_execution_replay_status": str(execution.get("replay_status") or ""),
			}
		)
		if _missing_fields(execution, REQUIRED_RAW_MESSAGE_ANALYSIS_EXECUTION_FIELDS):
			errors.append("analysis_execution_missing_fields")
		if not str(execution.get("run_id") or "").strip():
			errors.append("analysis_execution_run_id_missing")
		if execution.get("execution_status") != "completed":
			errors.append("analysis_execution_status_not_completed")
		if execution.get("execution_source") != VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_SOURCE:
			errors.append("analysis_execution_source_not_validator_owned")
		if execution.get("execution_version") != VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_VERSION:
			errors.append("analysis_execution_version_invalid")
		if execution.get("analyzer_id") != analysis.get("validator_safety_analyzer_id"):
			errors.append("analysis_execution_analyzer_id_mismatch")
		if execution.get("analyzer_version") != analysis.get("validator_safety_analyzer_version"):
			errors.append("analysis_execution_analyzer_version_mismatch")
		if analyzer_entry is None or analyzer_entry.get("registry_status") != "approved":
			errors.append("analysis_execution_analyzer_not_approved")
		elif execution.get("analyzer_version") not in _registry_values(analyzer_entry, "approved_analyzer_versions"):
			errors.append("analysis_execution_analyzer_version_not_approved")
		if not execution.get("input_hash"):
			errors.append("analysis_execution_input_hash_missing")
		elif execution.get("input_hash") != expected_input_hash:
			errors.append("analysis_execution_input_hash_mismatch")
		if not execution.get("output_hash"):
			errors.append("analysis_execution_output_hash_missing")
		elif execution.get("output_hash") != expected_output_hash:
			errors.append("analysis_execution_output_hash_mismatch")
		if not str(execution.get("artifact_hash") or "").strip():
			errors.append("analysis_execution_artifact_hash_missing")
		if execution.get("trace_redaction_status") != TRACE_REDACTION_SAFE or _evidence_contains_raw_business_text(execution):
			errors.append("analysis_execution_trace_redaction_not_safe")
		if execution.get("replay_status") != "verified":
			errors.append("analysis_execution_replay_not_verified")
		computed_execution_payload_hash = raw_message_analysis_execution_payload_hash(execution)
		if execution.get("execution_payload_hash") != computed_execution_payload_hash:
			errors.append("analysis_execution_payload_hash_mismatch")
		if not execution.get("attestation"):
			errors.append("analysis_execution_attestation_missing")
		elif analyzer_entry and analyzer_entry.get("registry_status") == "approved" and str(analyzer_entry.get("attestation_secret") or ""):
			expected_attestation = raw_message_analysis_execution_attestation_hash(
				str(analyzer_entry["attestation_secret"]),
				computed_execution_payload_hash,
			)
			if execution.get("attestation") != expected_attestation:
				errors.append("analysis_execution_attestation_invalid")
		else:
			errors.append("analysis_execution_attestation_unverifiable")
	if errors:
		metadata["analysis_execution_blocking_reason"] = ";".join(errors)
	else:
		metadata["analysis_execution_blocking_reason"] = ""
	return errors, metadata


def _tokenized_exact_erp_targets(normalized_message: str) -> List[str]:
	targets: List[str] = []
	cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else " " for char in normalized_message)
	for token in cleaned.split():
		if token.startswith("ec7h-"):
			targets.append(token)
	return targets


def _replay_tokens(normalized_message: str) -> List[str]:
	cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else " " for char in normalized_message)
	return cleaned.split()


def _target_family(target: str) -> str:
	if target.startswith("ec7h-item-"):
		return TARGET_TYPE_ITEM
	if target.startswith("ec7h-sup-"):
		return TARGET_TYPE_SUPPLIER
	if target.startswith("ec7h-cust-"):
		return TARGET_TYPE_CUSTOMER
	if target.startswith("ec7h-sinv-"):
		return TARGET_TYPE_INVOICE
	return ""


def _has_positive_read_only_retrieval_action(tokens: List[str]) -> bool:
	prefixes = (
		("show",),
		("list",),
		("display",),
		("show", "me"),
		("please", "show"),
		("please", "list"),
		("please", "display"),
		("can", "you", "show"),
		("can", "you", "list"),
		("can", "you", "display"),
		("what", "is"),
	)
	return any(tuple(tokens[: len(prefix)]) == prefix for prefix in prefixes)


def _has_positive_read_only_followup_shape(tokens: List[str]) -> bool:
	followup_terms = {"above", "previous", "that", "this", "row", "table", "invoice"}
	followup_actions = {"show", "display", "open", "explain", "who", "what"}
	return bool(set(tokens) & followup_terms) and bool(set(tokens) & followup_actions)


def _safe_factual_lookup_shape(tokens: List[str], target: str) -> bool:
	family = _target_family(target)
	if not family or not _has_positive_read_only_retrieval_action(tokens):
		return False
	common_terms = {"show", "list", "display", "me", "please", "can", "you", "what", "is", "the", "for", target}
	token_set = set(tokens)
	if family == TARGET_TYPE_ITEM:
		shapes = (
			{"item", "sales"},
			{"item", "price"},
			{"price", "history"},
			{"item", "details"},
		)
	elif family == TARGET_TYPE_SUPPLIER:
		shapes = (
			{"payable", "status"},
			{"supplier", "details"},
		)
	elif family == TARGET_TYPE_CUSTOMER:
		shapes = (
			{"outstanding", "balance"},
			{"customer", "details"},
		)
	elif family == TARGET_TYPE_INVOICE:
		shapes = (
			{"invoice", "details"},
			{"details"},
		)
	else:
		return False
	for shape_terms in shapes:
		if shape_terms <= token_set and token_set <= (common_terms | shape_terms):
			return True
	return False


def _positive_replayed_safety_classification(normalized_message: str, targets: List[str]) -> Tuple[str, str]:
	tokens = _replay_tokens(normalized_message)
	unique_targets = sorted(set(targets))
	if not unique_targets:
		if _has_positive_read_only_followup_shape(tokens):
			return "positive_safe_read_only_followup", ""
		return "ambiguous_or_unproven", "validator_owned_replay_target_missing"
	if len(unique_targets) != 1:
		return "ambiguous_or_unproven", "validator_owned_replay_target_ambiguous"
	if _safe_factual_lookup_shape(tokens, unique_targets[0]):
		return "positive_safe_factual_lookup", ""
	return "ambiguous_or_unproven", "validator_owned_replay_positive_safe_factual_lookup_not_proven"


def _conservative_replay_alarm(normalized_message: str) -> str:
	padded = f" {normalized_message} "
	if "?" in normalized_message:
		return "interrogative_requires_non_factual_replay"
	for connector in (" and ", " then ", " also ", ";"):
		if connector in padded:
			return "connector_requires_replay_segmentation"
	return ""


def _replay_raw_message_safety(
	normalized_message: str,
	subject_hash: str,
	residual_segments: List[ResidualSegment],
	connector_coverage_status: str,
	pronoun_reference_status: str,
	analysis: Dict[str, Any],
	analyzer_entry: Optional[Dict[str, Any]],
) -> Dict[str, str]:
	config_hash = str((analyzer_entry or {}).get("replay_config_hash") or "")
	artifact_hash = str((analyzer_entry or {}).get("replay_artifact_hash") or "")
	blocking_reasons: List[str] = []
	if not config_hash:
		blocking_reasons.append("validator_owned_replay_config_missing")
	if not artifact_hash:
		blocking_reasons.append("validator_owned_replay_artifact_missing")
	if (analyzer_entry or {}).get("replay_source") != VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_SOURCE:
		blocking_reasons.append("validator_owned_replay_source_not_approved")
	if (analyzer_entry or {}).get("replay_version") != VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_VERSION:
		blocking_reasons.append("validator_owned_replay_version_not_approved")

	targets = _tokenized_exact_erp_targets(normalized_message)
	replay_classification, replay_classification_reason = _positive_replayed_safety_classification(
		normalized_message,
		targets,
	)
	clause_span_status = "complete" if not residual_segments else "incomplete"
	positive_safe_factual_lookup = replay_classification == "positive_safe_factual_lookup"
	conservative_alarm = _conservative_replay_alarm(normalized_message)
	if positive_safe_factual_lookup and conservative_alarm == "interrogative_requires_non_factual_replay":
		conservative_alarm = ""
	connector_status = "accounted" if connector_coverage_status == "complete" and not conservative_alarm else "unresolved"
	residual_status = "clear" if not residual_segments else "unresolved"
	reference_status = "resolved_or_not_required" if pronoun_reference_status == "complete" else "unresolved"
	secondary_intent_status = "none" if positive_safe_factual_lookup and not conservative_alarm else "unresolved"
	mixed_intent_status = "none" if positive_safe_factual_lookup and not conservative_alarm else "mixed_or_ambiguous"
	unsafe_domain_status = "none" if positive_safe_factual_lookup and not conservative_alarm else "unsafe_or_ambiguous"
	ambiguity_status = "none" if positive_safe_factual_lookup and not conservative_alarm else replay_classification
	if conservative_alarm:
		blocking_reasons.append(conservative_alarm)
	if not targets:
		blocking_reasons.append("validator_owned_replay_target_missing")
	if not positive_safe_factual_lookup:
		blocking_reasons.append(replay_classification_reason or "validator_owned_replay_positive_safe_factual_lookup_not_proven")
	if clause_span_status != "complete":
		blocking_reasons.append("validator_owned_replay_clause_span_incomplete")
	if connector_status != "accounted":
		blocking_reasons.append("validator_owned_replay_connector_unresolved")
	if residual_status != "clear":
		blocking_reasons.append("validator_owned_replay_residual_unresolved")
	if reference_status != "resolved_or_not_required":
		blocking_reasons.append("validator_owned_replay_reference_unresolved")
	if analysis.get("trace_redaction_status") != TRACE_REDACTION_SAFE:
		blocking_reasons.append("validator_owned_replay_trace_not_safe")

	return {
		"raw_message_clause_coverage_status": clause_span_status,
		"raw_message_connector_status": connector_status,
		"raw_message_residual_status": residual_status,
		"raw_message_reference_status": reference_status,
		"raw_message_secondary_intent_status": secondary_intent_status,
		"raw_message_mixed_intent_status": mixed_intent_status,
		"raw_message_unsafe_domain_status": unsafe_domain_status,
		"raw_message_ambiguity_status": ambiguity_status,
		"trace_redaction_status": TRACE_REDACTION_SAFE if analysis.get("trace_redaction_status") == TRACE_REDACTION_SAFE else "unsafe",
		"final_decision": "safe" if not blocking_reasons else "blocked",
		"blocking_reason": ";".join(blocking_reasons),
		"config_hash": config_hash,
		"artifact_hash": artifact_hash,
		"subject_hash": subject_hash,
		"source": VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_SOURCE,
		"version": VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_VERSION,
		"derived_from_proposer_roles": "false",
		"derived_from_verifier_roles": "false",
		"derived_from_semantic_safe_output": "false",
		"derived_from_lexical_allow_rules": "false",
	}


def _validate_replayed_raw_message_safety(
	replay_result: Dict[str, str],
	proof_entry: Dict[str, Any],
	analysis: Dict[str, Any],
) -> Tuple[List[str], Dict[str, str]]:
	errors: List[str] = []
	metadata = {
		"replayed_raw_message_safety_required": True,
		"replayed_raw_message_safety_status": "replayed",
		"replayed_raw_message_safety_source": replay_result["source"],
		"replayed_raw_message_safety_version": replay_result["version"],
		"replayed_raw_message_safety_config_hash": replay_result["config_hash"],
		"replayed_raw_message_safety_subject_hash": replay_result["subject_hash"],
		"replayed_raw_message_safety_final_decision": replay_result["final_decision"],
		"replayed_raw_message_safety_evidence_match_status": "matched",
		"replayed_raw_message_safety_blocking_reason": replay_result["blocking_reason"],
	}
	if replay_result["final_decision"] != "safe":
		errors.append("validator_owned_replayed_raw_message_safety_not_safe")
	if replay_result["raw_message_clause_coverage_status"] != proof_entry.get("raw_message_clause_coverage_status"):
		errors.append("validator_owned_replay_clause_coverage_contradicts_proof")
	if replay_result["raw_message_secondary_intent_status"] != proof_entry.get("raw_message_secondary_intent_status"):
		errors.append("validator_owned_replay_secondary_intent_contradicts_proof")
	if replay_result["raw_message_mixed_intent_status"] != proof_entry.get("raw_message_mixed_intent_status"):
		errors.append("validator_owned_replay_mixed_intent_contradicts_proof")
	if replay_result["raw_message_residual_status"] != proof_entry.get("raw_message_residual_status"):
		errors.append("validator_owned_replay_residual_contradicts_proof")
	if replay_result["raw_message_reference_status"] != proof_entry.get("raw_message_reference_status"):
		errors.append("validator_owned_replay_reference_contradicts_proof")
	if replay_result["raw_message_connector_status"] != analysis.get("raw_message_connector_status"):
		errors.append("validator_owned_replay_connector_contradicts_analysis")
	if replay_result["raw_message_unsafe_domain_status"] != analysis.get("raw_message_unsafe_ambiguity_status"):
		errors.append("validator_owned_replay_unsafe_domain_contradicts_analysis")
	if replay_result["trace_redaction_status"] != TRACE_REDACTION_SAFE:
		errors.append("validator_owned_replay_trace_not_safe")
	if errors:
		metadata["replayed_raw_message_safety_evidence_match_status"] = "mismatch"
		if not metadata["replayed_raw_message_safety_blocking_reason"]:
			metadata["replayed_raw_message_safety_blocking_reason"] = ";".join(errors)
	return errors, metadata


def _validate_verifier_provenance(
	verifier_envelope: Dict[str, Any],
	trusted_verifier_registry: Optional[Dict[str, Dict[str, Any]]],
) -> Tuple[List[str], Dict[str, str]]:
	errors: List[str] = []
	metadata = {
		"clause_role_verifier_provenance_status": VERIFIER_PROVENANCE_UNTRUSTED,
		"clause_role_verifier_payload_hash_status": VERIFIER_PAYLOAD_HASH_FAILED,
		"clause_role_verifier_attestation_status": VERIFIER_ATTESTATION_FAILED,
	}
	registry = _trusted_verifier_registry(trusted_verifier_registry)
	verifier_source = str(verifier_envelope.get("verifier_source") or "")
	verifier_prompt_version = str(verifier_envelope.get("verifier_prompt_version") or "")
	verifier_model_name = str(verifier_envelope.get("verifier_model_name") or "")
	entry = registry.get(verifier_source)
	if not entry or entry.get("registry_status") != "approved":
		errors.append("verifier_source_not_trusted")
	else:
		if verifier_prompt_version not in _registry_values(entry, "approved_prompt_versions"):
			errors.append("verifier_prompt_version_not_approved")
		if verifier_model_name not in _registry_values(entry, "allowed_model_names"):
			errors.append("verifier_model_name_not_allowed")
		trusted_secret = str(entry.get("attestation_secret") or "")
		if not trusted_secret:
			errors.append("trusted_verifier_attestation_secret_missing")

	computed_payload_hash = canonical_verifier_payload_hash(verifier_envelope)
	if verifier_envelope.get("verifier_payload_hash") == computed_payload_hash:
		metadata["clause_role_verifier_payload_hash_status"] = VERIFIER_PAYLOAD_HASH_MATCHED
	else:
		errors.append("verifier_payload_hash_mismatch")

	if not verifier_envelope.get("verifier_attestation"):
		errors.append("verifier_attestation_missing")
	elif entry and entry.get("registry_status") == "approved" and str(entry.get("attestation_secret") or ""):
		expected_attestation = verifier_attestation_hash(str(entry["attestation_secret"]), computed_payload_hash)
		if verifier_envelope.get("verifier_attestation") == expected_attestation:
			metadata["clause_role_verifier_attestation_status"] = VERIFIER_ATTESTATION_VERIFIED
		else:
			errors.append("verifier_attestation_invalid")
	else:
		errors.append("verifier_attestation_unverifiable")

	if not errors:
		metadata["clause_role_verifier_provenance_status"] = VERIFIER_PROVENANCE_TRUSTED
	return errors, metadata


def _validate_validator_owned_safety_proof(
	raw_message: Any,
	clauses: List[Dict[str, Any]],
	targets: List[Dict[str, Any]],
	references: List[Dict[str, Any]],
	residual_segments: List[ResidualSegment],
	connector_coverage_status: str,
	pronoun_reference_status: str,
	semantic_status: str,
	lexical_conservative_alarm: bool,
	aggregates: Dict[str, Any],
	proposal: Dict[str, Any],
	role_metadata: Dict[str, Any],
	validator_owned_safety_proof_registry: Optional[Dict[str, Dict[str, Any]]],
) -> Tuple[List[str], Dict[str, Any]]:
	errors: List[str] = []
	metadata = {
		"validator_owned_safety_proof_required": True,
		"validator_owned_safety_proof_status": "missing",
		"validator_owned_safety_proof_source": VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_SOURCE,
		"validator_owned_safety_proof_version": VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_PROOF_VERSION,
		"validator_owned_safety_proof_blocking_reason": "",
		"validator_owned_safe_route_authority_status": VALIDATOR_SAFE_ROUTE_BLOCKED_WITHOUT_PROOF,
		"validator_owned_safety_analyzer_id": "",
		"validator_owned_safety_analyzer_version": "",
		"validator_owned_raw_message_safety_status": "",
		"validator_owned_raw_message_clause_coverage_status": "",
		"validator_owned_raw_message_secondary_intent_status": "",
		"validator_owned_raw_message_mixed_intent_status": "",
		"validator_owned_raw_message_residual_status": "",
		"validator_owned_raw_message_reference_status": "",
		"validator_owned_safety_proof_basis": "",
		"validator_owned_safety_proof_attestation_status": SAFETY_PROOF_ATTESTATION_FAILED,
		"validator_owned_safety_proof_id": "",
		"validator_owned_safety_proof_subject_hash": "",
		"validator_owned_safety_proof_uniqueness_status": "unknown",
		"validator_owned_safety_proof_conflict_status": "unknown",
		"validator_owned_safety_proof_evidence_status": "unknown",
		"validator_owned_safety_proof_evidence_semantics_status": "unknown",
		"validator_owned_raw_message_analysis_required": True,
		"validator_owned_raw_message_analysis_status": "missing",
		"validator_owned_raw_message_analysis_source": VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_SOURCE,
		"validator_owned_raw_message_analysis_version": VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_VERSION,
		"validator_owned_raw_message_analysis_subject_hash": "",
		"validator_owned_raw_message_analysis_evidence_match_status": "unknown",
		"validator_owned_raw_message_analysis_blocking_reason": "validator_owned_raw_message_analysis_missing",
		"analysis_execution_required": True,
		"analysis_execution_status": "missing",
		"analysis_execution_source": VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_SOURCE,
		"analysis_execution_version": VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_VERSION,
		"analysis_execution_run_id": "",
		"analysis_execution_subject_hash": "",
		"analysis_execution_input_hash": "",
		"analysis_execution_output_hash": "",
		"analysis_execution_artifact_hash": "",
		"analysis_execution_replay_status": "",
		"analysis_execution_blocking_reason": "analysis_execution_missing",
		"replayed_raw_message_safety_required": True,
		"replayed_raw_message_safety_status": "missing",
		"replayed_raw_message_safety_source": VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_SOURCE,
		"replayed_raw_message_safety_version": VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_VERSION,
		"replayed_raw_message_safety_config_hash": "",
		"replayed_raw_message_safety_subject_hash": "",
		"replayed_raw_message_safety_final_decision": "blocked",
		"replayed_raw_message_safety_evidence_match_status": "unknown",
		"replayed_raw_message_safety_blocking_reason": "validator_owned_replay_missing",
		"role_verification_authority_effect": ROLE_VERIFICATION_AUTHORITY_EFFECT_CONSISTENCY_ONLY,
		"semantic_backstop_authority_effect": SEMANTIC_BACKSTOP_AUTHORITY_EFFECT_RESTRICT_ONLY,
		"lexical_evidence_authority_effect": LEXICAL_EVIDENCE_AUTHORITY_EFFECT_RESTRICT_ONLY,
	}
	if validator_owned_safety_proof_registry is not None:
		errors.append("validator_owned_safety_proof_registry_caller_supplied_not_allowed")
	if role_metadata.get("clause_role_verifier_provenance_status") != VERIFIER_PROVENANCE_TRUSTED:
		errors.append("validator_owned_safety_proof_verifier_not_trusted")
	if not clauses:
		errors.append("validator_owned_safety_proof_clause_structure_missing")
	if residual_segments:
		errors.append("validator_owned_safety_proof_residual_unresolved")
	if connector_coverage_status != "complete":
		errors.append("validator_owned_safety_proof_connector_unresolved")
	if pronoun_reference_status != "complete":
		errors.append("validator_owned_safety_proof_reference_unresolved")
	if semantic_status in {SEMANTIC_BACKSTOP_UNSAFE, SEMANTIC_BACKSTOP_AMBIGUOUS}:
		errors.append("validator_owned_safety_proof_semantic_restricted")
	if lexical_conservative_alarm:
		errors.append("validator_owned_safety_proof_lexical_alarm")
	if bool(proposal.get("mixed_intent_detected")):
		errors.append("validator_owned_safety_proof_mixed_intent")
	if aggregates["decision_intent"]:
		errors.append("validator_owned_safety_proof_decision_intent")
	if aggregates["advice_intent"]:
		errors.append("validator_owned_safety_proof_advice_intent")
	if aggregates["business_action_intent"]:
		errors.append("validator_owned_safety_proof_business_action_intent")
	if aggregates["policy_boundary_intent"]:
		errors.append("validator_owned_safety_proof_policy_boundary_intent")
	if aggregates["business_action_domain"] != DOMAIN_NONE or aggregates["policy_domain"] != DOMAIN_NONE:
		errors.append("validator_owned_safety_proof_unsafe_domain")
	if aggregates["ambiguity_status"] != "none":
		errors.append("validator_owned_safety_proof_ambiguous")
	for clause in clauses:
		if clause["clause_type"] != CLAUSE_TYPE_FACTUAL_LOOKUP:
			errors.append("validator_owned_safety_proof_non_factual_clause")
			break
		if not clause["factual_lookup_intent"]:
			errors.append("validator_owned_safety_proof_missing_factual_intent")
			break
		if (
			clause["safe_followup_intent"]
			or clause["decision_intent"]
			or clause["advice_intent"]
			or clause["business_action_intent"]
			or clause["policy_boundary_intent"]
			or clause["business_action_domain"] != DOMAIN_NONE
			or clause["policy_domain"] != DOMAIN_NONE
			or clause["ambiguity_status"] != "none"
		):
			errors.append("validator_owned_safety_proof_factual_clause_not_pure")
			break

	registry = _trusted_safety_proof_registry(validator_owned_safety_proof_registry)
	raw_hash = hash_text(raw_message)
	normalized_hash = hash_text(normalize_message(raw_message))
	subject_hash = raw_message_safety_proof_subject_hash(raw_hash, normalized_hash)
	metadata["validator_owned_safety_proof_subject_hash"] = subject_hash
	approved_matches: List[Tuple[str, Dict[str, Any]]] = []
	for registry_key, candidate in registry.items():
		if not isinstance(candidate, dict):
			continue
		if candidate.get("registry_status") != "approved":
			continue
		if candidate.get("raw_message_hash") == raw_hash and candidate.get("normalized_message_hash") == normalized_hash:
			approved_matches.append((str(registry_key), candidate))
	if not approved_matches:
		errors.append("validator_owned_safety_proof_missing")
		metadata["validator_owned_safety_proof_uniqueness_status"] = "no_matching_proof"
		metadata["validator_owned_safety_proof_conflict_status"] = "none"
	elif len(approved_matches) > 1:
		errors.append("validator_owned_safety_proof_conflict_detected")
		metadata["validator_owned_safety_proof_uniqueness_status"] = "duplicate_subject"
		metadata["validator_owned_safety_proof_conflict_status"] = "conflict_detected"
		proof_entry = approved_matches[0][1]
	else:
		registry_key, proof_entry = approved_matches[0]
		metadata["validator_owned_safety_proof_uniqueness_status"] = "unique"
		metadata["validator_owned_safety_proof_conflict_status"] = "none"
		missing = _missing_fields(proof_entry, REQUIRED_RAW_MESSAGE_SAFETY_PROOF_FIELDS)
		if missing:
			errors.append("validator_owned_safety_proof_missing_raw_message_fields")
		proof_id = str(proof_entry.get("safety_proof_id") or "")
		metadata["validator_owned_safety_proof_id"] = proof_id
		metadata.update(
			{
				"validator_owned_safety_analyzer_id": str(proof_entry.get("validator_safety_analyzer_id") or ""),
				"validator_owned_safety_analyzer_version": str(proof_entry.get("validator_safety_analyzer_version") or ""),
				"validator_owned_raw_message_safety_status": str(proof_entry.get("raw_message_safety_status") or ""),
				"validator_owned_raw_message_clause_coverage_status": str(
					proof_entry.get("raw_message_clause_coverage_status") or ""
				),
				"validator_owned_raw_message_secondary_intent_status": str(
					proof_entry.get("raw_message_secondary_intent_status") or ""
				),
				"validator_owned_raw_message_mixed_intent_status": str(
					proof_entry.get("raw_message_mixed_intent_status") or ""
				),
				"validator_owned_raw_message_residual_status": str(proof_entry.get("raw_message_residual_status") or ""),
				"validator_owned_raw_message_reference_status": str(proof_entry.get("raw_message_reference_status") or ""),
				"validator_owned_safety_proof_basis": str(proof_entry.get("safety_proof_basis") or ""),
			}
		)
		if not proof_id:
			errors.append("validator_owned_safety_proof_id_missing")
		if str(registry_key) != proof_id:
			errors.append("validator_owned_safety_proof_registry_key_mismatch")
		if proof_entry.get("safety_proof_subject_hash") != subject_hash:
			errors.append("validator_owned_safety_proof_subject_hash_mismatch")
		analyzer_id = str(proof_entry.get("validator_safety_analyzer_id") or "")
		analyzer_version = str(proof_entry.get("validator_safety_analyzer_version") or "")
		analyzer_entry = VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY.get(analyzer_id)
		if not analyzer_entry or analyzer_entry.get("registry_status") != "approved":
			errors.append("validator_owned_safety_analyzer_not_trusted")
		else:
			if analyzer_version not in _registry_values(analyzer_entry, "approved_analyzer_versions"):
				errors.append("validator_owned_safety_analyzer_version_not_approved")
			secret = str(analyzer_entry.get("attestation_secret") or "")
			if not secret:
				errors.append("validator_owned_safety_analyzer_attestation_secret_missing")
		if proof_entry.get("raw_message_safety_status") != "safe":
			errors.append("validator_owned_raw_message_safety_not_safe")
		if proof_entry.get("raw_message_clause_coverage_status") != "complete":
			errors.append("validator_owned_raw_message_clause_coverage_not_complete")
		if proof_entry.get("raw_message_secondary_intent_status") != "none":
			errors.append("validator_owned_raw_message_secondary_intent_not_clear")
		if proof_entry.get("raw_message_mixed_intent_status") != "none":
			errors.append("validator_owned_raw_message_mixed_intent_not_clear")
		if proof_entry.get("raw_message_residual_status") != "clear":
			errors.append("validator_owned_raw_message_residual_not_clear")
		if proof_entry.get("raw_message_reference_status") != "resolved_or_not_required":
			errors.append("validator_owned_raw_message_reference_not_clear")
		evidence_fields = (
			"raw_message_safety_evidence_hash",
			"raw_message_clause_boundary_evidence_hash",
			"raw_message_secondary_intent_evidence_hash",
			"raw_message_residual_evidence_hash",
			"raw_message_reference_evidence_hash",
		)
		if all(str(proof_entry.get(field_name) or "").strip() for field_name in evidence_fields):
			metadata["validator_owned_safety_proof_evidence_status"] = "present"
		else:
			errors.append("validator_owned_safety_proof_evidence_missing")
			metadata["validator_owned_safety_proof_evidence_status"] = "missing"
		evidence_errors, evidence_semantics_status = _validate_raw_message_safety_evidence_objects(
			proof_entry,
			analyzer_id,
			analyzer_version,
		)
		errors.extend(evidence_errors)
		metadata["validator_owned_safety_proof_evidence_semantics_status"] = evidence_semantics_status
		analysis_errors, analysis_metadata = _validate_validator_owned_raw_message_analysis(
			proof_entry,
			normalize_message(raw_message),
			raw_hash,
			normalized_hash,
			subject_hash,
			residual_segments,
			connector_coverage_status,
			pronoun_reference_status,
		)
		errors.extend(analysis_errors)
		metadata.update(analysis_metadata)
		if proof_entry.get("safe_route_authority") != ANSWER_MODE_GOVERNED_ERP:
			errors.append("validator_owned_safety_proof_route_authority_invalid")
		if proof_entry.get("safety_proof_basis") != RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE:
			errors.append("validator_owned_safety_proof_derived_from_clause_roles")
		computed_payload_hash = raw_message_safety_proof_payload_hash(proof_entry)
		if proof_entry.get("safety_proof_payload_hash") != computed_payload_hash:
			errors.append("validator_owned_safety_proof_payload_hash_mismatch")
		elif proof_id and proof_id != computed_payload_hash:
			errors.append("validator_owned_safety_proof_id_hash_mismatch")
		elif analyzer_entry and analyzer_entry.get("registry_status") == "approved" and str(analyzer_entry.get("attestation_secret") or ""):
			expected_attestation = raw_message_safety_proof_attestation_hash(
				str(analyzer_entry["attestation_secret"]),
				computed_payload_hash,
			)
			if proof_entry.get("safety_proof_attestation") == expected_attestation:
				metadata["validator_owned_safety_proof_attestation_status"] = SAFETY_PROOF_ATTESTATION_VERIFIED
			else:
				errors.append("validator_owned_safety_proof_attestation_invalid")

	if errors:
		metadata["validator_owned_safety_proof_status"] = "failed"
		metadata["validator_owned_safety_proof_blocking_reason"] = ";".join(errors)
	else:
		metadata["validator_owned_safety_proof_status"] = "passed"
		metadata["validator_owned_safety_proof_blocking_reason"] = ""
		metadata["validator_owned_safe_route_authority_status"] = VALIDATOR_SAFE_ROUTE_PROVEN
	return errors, metadata


def _proposal_completeness_errors(proposal: Dict[str, Any], clauses: List[Dict[str, Any]], normalized_message: str) -> List[str]:
	errors: List[str] = []
	mechanical_status, _ = _validator_owned_mechanical_status(proposal.get("mechanical_command_id"))
	if proposal.get("proposal_completeness_status") != COMPLETENESS_STATUS_COMPLETE:
		errors.append("proposal_completeness_not_complete")
	if proposal.get("clause_segmentation_status") != AUDIT_STATUS_PASSED:
		errors.append("clause_segmentation_audit_not_passed")
	if proposal.get("secondary_intent_audit_status") != AUDIT_STATUS_PASSED:
		errors.append("secondary_intent_audit_not_passed")
	if proposal.get("residual_audit_status") != AUDIT_STATUS_PASSED:
		errors.append("residual_audit_not_passed")
	if proposal.get("clause_role_confidence_status") != AUDIT_STATUS_PASSED:
		errors.append("clause_role_confidence_not_passed")
	if proposal.get("independent_parse_guard_status") != AUDIT_STATUS_PASSED:
		errors.append("independent_parse_guard_not_passed")
	if not isinstance(proposal.get("natural_language_interpretation_required"), bool):
		errors.append("natural_language_interpretation_required_not_boolean")

	full_span_factual = _is_full_span_factual_clause(clauses, normalized_message)
	if full_span_factual:
		# Full-span factual natural language can only be report-eligible when
		# the separate verifier envelope validates the same role. Proposer
		# mechanical claims are retained as trace fields but are not authority.
		_ = mechanical_status
	else:
		if proposal.get("full_span_factual_authority") not in {
			FULL_SPAN_FACTUAL_AUTHORITY_NOT_ALLOWED,
			"not_required",
		}:
			errors.append("full_span_factual_authority_invalid_for_segmented_proposal")
	return errors


def _validate_clause_role_verification(
	proposal: Dict[str, Any],
	clauses: List[Dict[str, Any]],
	raw_message: Any,
	normalized_message: str,
	verifier_envelope: Optional[Dict[str, Any]],
	trusted_verifier_registry: Optional[Dict[str, Dict[str, Any]]],
) -> Tuple[List[str], Dict[str, Any], Dict[str, Dict[str, Any]]]:
	errors: List[str] = []
	metadata = {
		"clause_role_verification_required": True,
		"clause_role_verifier_source": "",
		"clause_role_verifier_run_id": "",
		"clause_role_verifier_model_name": "",
		"clause_role_verifier_prompt_version": "",
		"clause_role_verifier_payload_hash": "",
		"clause_role_verifier_status": "",
		"clause_role_verifier_independence_status": "",
		"clause_role_verifier_authority_effect": "",
		"clause_role_verifier_provenance_status": VERIFIER_PROVENANCE_UNTRUSTED,
		"clause_role_verifier_payload_hash_status": VERIFIER_PAYLOAD_HASH_FAILED,
		"clause_role_verifier_attestation_status": VERIFIER_ATTESTATION_FAILED,
		"all_clause_roles_verified": False,
		"proposer_verifier_agreement_status": "",
		"role_disagreement_policy": ROLE_DISAGREEMENT_POLICY_FAIL_CLOSED,
		"role_verification_blocking_reason": "",
		"natural_language_report_authority_status": NATURAL_LANGUAGE_REPORT_AUTHORITY_BLOCKED_WITHOUT_VERIFIER,
	}
	verified_by_clause_id: Dict[str, Dict[str, Any]] = {}
	if verifier_envelope is None:
		errors.append("external_verifier_envelope_missing")
		metadata["role_verification_blocking_reason"] = ";".join(errors)
		return errors, metadata, verified_by_clause_id
	if not isinstance(verifier_envelope, dict):
		errors.append("external_verifier_envelope_not_object")
		metadata["role_verification_blocking_reason"] = ";".join(errors)
		return errors, metadata, verified_by_clause_id
	missing = _missing_fields(verifier_envelope, REQUIRED_VERIFIER_ENVELOPE_FIELDS)
	if missing:
		errors.append("external_verifier_envelope_missing_fields")
	proposer_source = str(proposal.get("proposal_authority_source") or "")
	proposer_model_name = str(proposal.get("intent_proposer_model_name") or "")
	proposer_run_id = str(proposal.get("intent_proposer_run_id") or "")
	verifier_source = str(verifier_envelope.get("verifier_source") or "")
	verifier_run_id = str(verifier_envelope.get("verifier_run_id") or "")
	metadata.update(
		{
			"clause_role_verifier_source": verifier_source,
			"clause_role_verifier_run_id": verifier_run_id,
			"clause_role_verifier_model_name": str(verifier_envelope.get("verifier_model_name") or ""),
			"clause_role_verifier_prompt_version": str(verifier_envelope.get("verifier_prompt_version") or ""),
			"clause_role_verifier_payload_hash": str(verifier_envelope.get("verifier_payload_hash") or ""),
			"clause_role_verifier_status": str(verifier_envelope.get("verifier_status") or ""),
			"clause_role_verifier_independence_status": str(verifier_envelope.get("verifier_independence_status") or ""),
			"clause_role_verifier_authority_effect": str(verifier_envelope.get("verifier_authority_effect") or ""),
		}
	)
	provenance_errors, provenance_metadata = _validate_verifier_provenance(
		verifier_envelope,
		trusted_verifier_registry,
	)
	errors.extend(provenance_errors)
	metadata.update(provenance_metadata)
	if verifier_envelope.get("raw_message_hash") != hash_text(raw_message):
		errors.append("verifier_envelope_raw_hash_mismatch")
	if verifier_envelope.get("normalized_message_hash") != hash_text(normalized_message):
		errors.append("verifier_envelope_normalized_hash_mismatch")
	if not verifier_source:
		errors.append("clause_role_verifier_missing")
	if verifier_source and verifier_source in {proposer_source, proposer_model_name}:
		errors.append("clause_role_verifier_source_not_independent")
	if not verifier_run_id:
		errors.append("clause_role_verifier_run_id_missing")
	if verifier_run_id and proposer_run_id and verifier_run_id == proposer_run_id:
		errors.append("clause_role_verifier_run_id_not_independent")
	if not str(verifier_envelope.get("verifier_model_name") or ""):
		errors.append("clause_role_verifier_model_name_missing")
	if not str(verifier_envelope.get("verifier_prompt_version") or ""):
		errors.append("clause_role_verifier_prompt_version_missing")
	if verifier_envelope.get("verifier_status") != AUDIT_STATUS_PASSED:
		errors.append("clause_role_verifier_status_not_passed")
	if verifier_envelope.get("verifier_independence_status") != "independent":
		errors.append("clause_role_verifier_not_independent")
	if verifier_envelope.get("verifier_authority_effect") != VERIFIER_AUTHORITY_EFFECT_CONSISTENCY_ONLY:
		errors.append("clause_role_verifier_authority_effect_invalid")
	if not str(verifier_envelope.get("verifier_payload_hash") or ""):
		errors.append("clause_role_verifier_payload_hash_missing")
	if verifier_envelope.get("trace_redaction_status") != TRACE_REDACTION_SAFE:
		errors.append("clause_role_verifier_trace_not_safe")

	verified_clauses = verifier_envelope.get("verified_clauses")
	if not isinstance(verified_clauses, list):
		errors.append("verified_clauses_not_list")
		verified_clauses = []
	for verified_clause in verified_clauses:
		if not isinstance(verified_clause, dict):
			errors.append("verified_clause_not_object")
			continue
		missing = _missing_fields(verified_clause, REQUIRED_VERIFIED_CLAUSE_FIELDS)
		if missing:
			errors.append("verified_clause_missing_fields")
			continue
		clause_id = str(verified_clause.get("clause_id") or "")
		if clause_id in verified_by_clause_id:
			errors.append("duplicate_verified_clause_id")
		verified_by_clause_id[clause_id] = verified_clause
	if len(verified_by_clause_id) != len(clauses):
		errors.append("verifier_clause_map_incomplete")
	for clause in clauses:
		verified_clause = verified_by_clause_id.get(str(clause.get("clause_id") or ""))
		if not verified_clause:
			errors.append("clause_missing_external_verification")
			continue
		if verified_clause["span_start"] != clause["start"] or verified_clause["span_end"] != clause["end"]:
			errors.append("verified_clause_span_mismatch")
		normalized_clause = normalized_message[clause["start"] : clause["end"]]
		if verified_clause["normalized_clause_hash"] != hash_text(normalized_clause):
			errors.append("verified_clause_hash_mismatch")
		if verified_clause["verified_clause_type"] not in VALID_CLAUSE_TYPES:
			errors.append("invalid_verified_clause_type")
		if verified_clause["verified_business_action_domain"] not in VALID_BUSINESS_ACTION_DOMAINS:
			errors.append("invalid_verified_business_action_domain")
		if verified_clause["verified_policy_domain"] not in VALID_BUSINESS_ACTION_DOMAINS:
			errors.append("invalid_verified_policy_domain")
		if verified_clause["verification_status"] != "verified":
			errors.append("clause_role_not_verified")
		try:
			verification_confidence = float(verified_clause.get("verification_confidence"))
		except (TypeError, ValueError):
			verification_confidence = -1.0
		if verification_confidence < MIN_PROPOSER_CONFIDENCE:
			errors.append("clause_role_verification_confidence_too_low")
		comparisons = (
			("clause_type", "verified_clause_type"),
			("factual_lookup_intent", "verified_factual_lookup_intent"),
			("safe_followup_intent", "verified_safe_followup_intent"),
			("decision_intent", "verified_decision_intent"),
			("advice_intent", "verified_advice_intent"),
			("business_action_intent", "verified_business_action_intent"),
			("policy_boundary_intent", "verified_policy_boundary_intent"),
			("business_action_domain", "verified_business_action_domain"),
			("policy_domain", "verified_policy_domain"),
		)
		for proposed_key, verified_key in comparisons:
			proposed_value = clause.get(proposed_key)
			verified_value = verified_clause.get(verified_key)
			if isinstance(proposed_value, bool):
				if bool(proposed_value) != bool(verified_value):
					errors.append("proposer_verifier_role_disagreement")
					break
			elif str(proposed_value) != str(verified_value):
				errors.append("proposer_verifier_role_disagreement")
				break
	metadata["all_clause_roles_verified"] = bool(clauses and not errors)
	metadata["proposer_verifier_agreement_status"] = AUDIT_STATUS_PASSED if not errors else "failed"
	metadata["role_verification_blocking_reason"] = ";".join(errors)
	metadata["natural_language_report_authority_status"] = (
		NATURAL_LANGUAGE_REPORT_AUTHORITY_VERIFIED
		if not errors
		else NATURAL_LANGUAGE_REPORT_AUTHORITY_BLOCKED_WITHOUT_VERIFIER
	)
	return errors, metadata, verified_by_clause_id


def _aggregate_contract_intents(clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
	domains = [clause["business_action_domain"] for clause in clauses if clause["business_action_domain"] != DOMAIN_NONE]
	policy_domains = [clause["policy_domain"] for clause in clauses if clause["policy_domain"] != DOMAIN_NONE]
	return {
		"factual_lookup_intent": any(bool(clause["factual_lookup_intent"]) for clause in clauses),
		"safe_followup_intent": any(bool(clause["safe_followup_intent"]) for clause in clauses),
		"decision_intent": any(bool(clause["decision_intent"]) for clause in clauses),
		"advice_intent": any(bool(clause["advice_intent"]) for clause in clauses),
		"business_action_intent": any(bool(clause["business_action_intent"]) for clause in clauses),
		"policy_boundary_intent": any(bool(clause["policy_boundary_intent"]) for clause in clauses),
		"business_action_domain": domains[0] if domains else DOMAIN_NONE,
		"policy_domain": policy_domains[0] if policy_domains else DOMAIN_NONE,
		"ambiguity_status": "ambiguous" if any(clause["ambiguity_status"] != "none" for clause in clauses) else "none",
	}


def _clauses_with_external_verification(
	clauses: List[Dict[str, Any]],
	verified_by_clause_id: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
	enriched: List[Dict[str, Any]] = []
	for clause in clauses:
		merged = dict(clause)
		verified_clause = verified_by_clause_id.get(str(clause.get("clause_id") or ""))
		if verified_clause:
			merged.update(
				{
					"verified_clause_type": verified_clause.get("verified_clause_type"),
					"verified_factual_lookup_intent": verified_clause.get("verified_factual_lookup_intent"),
					"verified_safe_followup_intent": verified_clause.get("verified_safe_followup_intent"),
					"verified_decision_intent": verified_clause.get("verified_decision_intent"),
					"verified_advice_intent": verified_clause.get("verified_advice_intent"),
					"verified_business_action_intent": verified_clause.get("verified_business_action_intent"),
					"verified_policy_boundary_intent": verified_clause.get("verified_policy_boundary_intent"),
					"verified_business_action_domain": verified_clause.get("verified_business_action_domain"),
					"verified_policy_domain": verified_clause.get("verified_policy_domain"),
					"verification_status": verified_clause.get("verification_status"),
					"verification_confidence": verified_clause.get("verification_confidence"),
					"verification_blocking_reason": verified_clause.get("verification_blocking_reason"),
				}
			)
		enriched.append(merged)
	return enriched


def _answer_mode_for_domain(domain: str, ambiguity_status: str) -> str:
	if ambiguity_status != "none":
		return ANSWER_MODE_CLARIFICATION
	if domain in CONTROL_DOMAINS:
		return ANSWER_MODE_CONTROL_BOUNDARY
	if domain in POLICY_DOMAINS or domain != DOMAIN_NONE:
		return ANSWER_MODE_POLICY_BOUNDARY
	return ANSWER_MODE_GOVERNED_ERP


def _semantic_backstop(semantic_backstop: Optional[Dict[str, Any]]) -> Tuple[str, str, Optional[str]]:
	if not semantic_backstop:
		return SEMANTIC_BACKSTOP_MISSING, "none", None
	status = str(semantic_backstop.get("status") or SEMANTIC_BACKSTOP_MISSING)
	if status == SEMANTIC_BACKSTOP_SAFE:
		return status, "cannot_authorize", None
	if status in {SEMANTIC_BACKSTOP_UNSAFE, SEMANTIC_BACKSTOP_AMBIGUOUS}:
		return status, "restricted_routing", None
	return status, "invalid_semantic_backstop", "invalid_semantic_backstop"


def _validate_strict_deterministic_safe_subset(
	raw_message: Any,
	proof: Optional[Dict[str, Any]],
) -> Optional[IntentBoundaryContract]:
	if not proof:
		return None
	normalized = normalize_message(raw_message)
	required_flags = (
		"decision_intent",
		"advice_intent",
		"business_action_intent",
		"policy_boundary_intent",
		"legal_or_regulatory_advice_intent",
		"prediction_score_or_future_cause_intent",
		"manipulation_report_hiding_intent",
		"write_mutation_workflow_intent",
		"unsupported_business_recommendation_intent",
		"mixed_intent_detected",
		"visible_context_ambiguity",
		"unresolved_pronoun_or_reference",
		"unsafe_domain_evidence",
	)
	errors: List[str] = []
	mechanical_status, mechanical_command_id = _validator_owned_mechanical_status(proof.get("mechanical_command_id"))
	if proof.get("status") != "proven":
		errors.append("strict_safe_subset_not_proven")
	if proof.get("normalized_message_hash") != hash_text(normalized):
		errors.append("strict_safe_subset_hash_mismatch")
	if proof.get("factual_lookup_intent") is not True:
		errors.append("strict_safe_subset_missing_factual_lookup")
	for flag in required_flags:
		if proof.get(flag) is not False:
			errors.append(f"strict_safe_subset_flag_not_false:{flag}")
	if proof.get("clause_coverage_status") != "complete":
		errors.append("strict_safe_subset_coverage_not_complete")
	if proof.get("target_schema_status") != "valid":
		errors.append("strict_safe_subset_target_schema_not_valid")
	if proof.get("trace_redaction_status") != TRACE_REDACTION_SAFE:
		errors.append("strict_safe_subset_trace_not_safe")
	if proof.get("safe_subset_authority_source") != PROPOSAL_SOURCE_DETERMINISTIC_SAFE_SUBSET:
		errors.append("strict_safe_subset_invalid_authority_source")
	if proof.get("mechanical_safe_subset_status") != "preapproved_mechanical_command":
		errors.append("strict_safe_subset_not_mechanical_authority")
	if proof.get("mechanical_command_id") is None:
		errors.append("strict_safe_subset_missing_mechanical_command_id")
	if mechanical_status != "validator_owned_approved":
		errors.append("strict_safe_subset_command_not_validator_owned")
	if proof.get("mechanical_command_registry_status") == "approved" and mechanical_status != "validator_owned_approved":
		errors.append("strict_safe_subset_proof_supplied_registry_status_not_authoritative")
	if proof.get("mechanical_command_registry_status") != "approved":
		errors.append("strict_safe_subset_mechanical_command_not_approved")
	if proof.get("natural_language_interpretation_required") is not False:
		errors.append("strict_safe_subset_natural_language_not_allowed")
	if proof.get("intent_interpretation_required") is not False:
		errors.append("strict_safe_subset_requires_intent_interpretation")
	if errors:
		return _invalid_contract(
			raw_message,
			errors,
			intent_proposer_role="deterministic_safe_subset",
			intent_proposer_status=str(proof.get("status") or ""),
			proposal_authority_source=str(proof.get("safe_subset_authority_source") or ""),
			proposal_completeness_status=str(proof.get("proposal_completeness_status") or ""),
			clause_segmentation_status=str(proof.get("clause_segmentation_status") or ""),
			secondary_intent_audit_status=str(proof.get("secondary_intent_audit_status") or ""),
			residual_audit_status=str(proof.get("residual_audit_status") or ""),
			clause_role_confidence_status=str(proof.get("clause_role_confidence_status") or ""),
			full_span_factual_authority=str(proof.get("full_span_factual_authority") or ""),
			full_span_factual_allow_reason=str(proof.get("full_span_factual_allow_reason") or ""),
			natural_language_interpretation_required=bool(proof.get("natural_language_interpretation_required", True)),
			independent_parse_guard_status=str(proof.get("independent_parse_guard_status") or ""),
			validator_owned_mechanical_authority_status=mechanical_status,
			validator_owned_mechanical_command_id=mechanical_command_id,
			clause_role_verification_required=False,
			natural_language_report_authority_status=NATURAL_LANGUAGE_REPORT_AUTHORITY_BLOCKED_WITHOUT_VERIFIER,
			trace_redaction_status=str(proof.get("trace_redaction_status") or "unknown"),
		)
	targets = proof.get("erp_targets") if isinstance(proof.get("erp_targets"), list) else []
	return IntentBoundaryContract(
		contract_version=CONTRACT_VERSION,
		raw_message_hash=hash_text(raw_message),
		normalized_message_hash=hash_text(normalized),
		clause_count=int(proof.get("clause_count") or 1),
		clauses=[],
		erp_targets=[_redact_target(target) for target in targets if isinstance(target, dict) and set(REQUIRED_TARGET_FIELDS) <= set(target)],
		visible_context_references=[],
		factual_lookup_intent=True,
		safe_followup_intent=False,
		decision_intent=False,
		advice_intent=False,
		business_action_intent=False,
		policy_boundary_intent=False,
		mixed_intent_detected=False,
		business_action_domain=DOMAIN_NONE,
		policy_domain=DOMAIN_NONE,
		ambiguity_status="none",
		report_routing_allowed=True,
		context_reuse_allowed=False,
		model_reasoning_allowed=True,
		final_emission_allowed=True,
		required_answer_mode=ANSWER_MODE_GOVERNED_ERP,
		boundary_reason="strict_deterministic_safe_subset_proven",
		validator_status=DETERMINISTIC_VALIDATOR_VALID,
		trace_redaction_status=TRACE_REDACTION_SAFE,
		intent_proposer_role="deterministic_safe_subset",
		intent_proposer_status="proven",
		intent_proposer_confidence=1.0,
		intent_proposer_model_name="deterministic_safe_subset",
		intent_proposer_output_status=PROPOSER_OUTPUT_VALID,
		proposal_authority_source=PROPOSAL_SOURCE_DETERMINISTIC_SAFE_SUBSET,
		proposal_completeness_status=COMPLETENESS_STATUS_COMPLETE,
		clause_segmentation_status=AUDIT_STATUS_PASSED,
		secondary_intent_audit_status=AUDIT_STATUS_PASSED,
		residual_audit_status=AUDIT_STATUS_PASSED,
		clause_role_confidence_status=AUDIT_STATUS_PASSED,
		full_span_factual_authority=FULL_SPAN_FACTUAL_AUTHORITY_MECHANICAL_ONLY,
		full_span_factual_allow_reason="preapproved_mechanical_command",
		natural_language_interpretation_required=False,
		independent_parse_guard_status=AUDIT_STATUS_PASSED,
		lexical_authority_effect=LEXICAL_AUTHORITY_EFFECT_NONE,
		lexical_conservative_alarm=False,
		lexical_alarm_reason="",
		validator_owned_mechanical_authority_status=mechanical_status,
		validator_owned_mechanical_command_id=mechanical_command_id,
		clause_role_verification_required=False,
		clause_role_verifier_source="validator_owned_mechanical_registry",
		clause_role_verifier_run_id=mechanical_command_id,
		clause_role_verifier_model_name="validator_owned_mechanical_registry",
		clause_role_verifier_prompt_version="registry",
		clause_role_verifier_payload_hash=hash_text(mechanical_command_id),
		clause_role_verifier_status=AUDIT_STATUS_PASSED,
		clause_role_verifier_independence_status="independent",
		clause_role_verifier_authority_effect=VERIFIER_AUTHORITY_EFFECT_CONSISTENCY_ONLY,
		clause_role_verifier_provenance_status=VERIFIER_PROVENANCE_TRUSTED,
		clause_role_verifier_payload_hash_status=VERIFIER_PAYLOAD_HASH_MATCHED,
		clause_role_verifier_attestation_status=VERIFIER_ATTESTATION_VERIFIED,
		all_clause_roles_verified=True,
		proposer_verifier_agreement_status=AUDIT_STATUS_PASSED,
		role_disagreement_policy=ROLE_DISAGREEMENT_POLICY_FAIL_CLOSED,
		role_verification_blocking_reason="",
		natural_language_report_authority_status=NATURAL_LANGUAGE_REPORT_AUTHORITY_VERIFIED,
		validator_owned_safety_proof_required=True,
		validator_owned_safety_proof_status="passed",
		validator_owned_safety_proof_source="validator_owned_mechanical_registry",
		validator_owned_safety_proof_version="mechanical_registry",
		validator_owned_safety_proof_blocking_reason="",
		validator_owned_safe_route_authority_status=VALIDATOR_SAFE_ROUTE_PROVEN,
		validator_owned_safety_analyzer_id="validator_owned_mechanical_registry",
		validator_owned_safety_analyzer_version="mechanical_registry",
		validator_owned_raw_message_safety_status="safe",
		validator_owned_raw_message_clause_coverage_status="complete",
		validator_owned_raw_message_secondary_intent_status="none",
		validator_owned_raw_message_mixed_intent_status="none",
		validator_owned_raw_message_residual_status="clear",
		validator_owned_raw_message_reference_status="resolved_or_not_required",
		validator_owned_safety_proof_basis="validator_owned_mechanical_command_registry",
		validator_owned_safety_proof_attestation_status=SAFETY_PROOF_ATTESTATION_VERIFIED,
		validator_owned_safety_proof_id=mechanical_command_id,
		validator_owned_safety_proof_subject_hash=hash_text(mechanical_command_id),
		validator_owned_safety_proof_uniqueness_status="mechanical_registry_unique",
		validator_owned_safety_proof_conflict_status="none",
	validator_owned_safety_proof_evidence_status="mechanical_registry",
	validator_owned_safety_proof_evidence_semantics_status="mechanical_registry",
	validator_owned_raw_message_analysis_required=False,
	validator_owned_raw_message_analysis_status="mechanical_registry",
	validator_owned_raw_message_analysis_source="validator_owned_mechanical_registry",
	validator_owned_raw_message_analysis_version="mechanical_registry",
	validator_owned_raw_message_analysis_subject_hash=hash_text(mechanical_command_id),
	validator_owned_raw_message_analysis_evidence_match_status="mechanical_registry",
	validator_owned_raw_message_analysis_blocking_reason="",
	analysis_execution_required=False,
	analysis_execution_status="mechanical_registry",
	analysis_execution_source="validator_owned_mechanical_registry",
	analysis_execution_version="mechanical_registry",
	analysis_execution_run_id=mechanical_command_id,
	analysis_execution_subject_hash=hash_text(mechanical_command_id),
	analysis_execution_input_hash=hash_text(mechanical_command_id),
	analysis_execution_output_hash=hash_text(mechanical_command_id),
	analysis_execution_artifact_hash=hash_text(mechanical_command_id),
	analysis_execution_replay_status="mechanical_registry",
	analysis_execution_blocking_reason="",
	replayed_raw_message_safety_required=False,
	replayed_raw_message_safety_status="mechanical_registry",
	replayed_raw_message_safety_source="validator_owned_mechanical_registry",
	replayed_raw_message_safety_version="mechanical_registry",
	replayed_raw_message_safety_config_hash=hash_text(mechanical_command_id),
	replayed_raw_message_safety_subject_hash=hash_text(mechanical_command_id),
	replayed_raw_message_safety_final_decision="safe",
	replayed_raw_message_safety_evidence_match_status="mechanical_registry",
	replayed_raw_message_safety_blocking_reason="",
	role_verification_authority_effect=ROLE_VERIFICATION_AUTHORITY_EFFECT_CONSISTENCY_ONLY,
		semantic_backstop_authority_effect=SEMANTIC_BACKSTOP_AUTHORITY_EFFECT_RESTRICT_ONLY,
		lexical_evidence_authority_effect=LEXICAL_EVIDENCE_AUTHORITY_EFFECT_RESTRICT_ONLY,
		deterministic_validator_status=DETERMINISTIC_VALIDATOR_VALID,
		deterministic_validator_errors=[],
		semantic_backstop_status=SEMANTIC_BACKSTOP_MISSING,
		semantic_backstop_effect="none",
		authority_source=AUTHORITY_SOURCE_STRICT_DETERMINISTIC_SAFE_SUBSET,
		authority_decision=AUTHORITY_DECISION_ALLOW_REPORT,
		authority_blocking_reason="",
		residual_text_status="accounted",
		strict_deterministic_safe_subset_status="proven",
	)


def validate_intent_boundary_contract(
	raw_message: Any,
	proposal: Optional[Dict[str, Any]],
	*,
	semantic_backstop: Optional[Dict[str, Any]] = None,
	strict_deterministic_safe_subset: Optional[Dict[str, Any]] = None,
	verifier_envelope: Optional[Dict[str, Any]] = None,
	trusted_verifier_registry: Optional[Dict[str, Dict[str, Any]]] = None,
	validator_owned_safety_proof_registry: Optional[Dict[str, Dict[str, Any]]] = None,
) -> IntentBoundaryContract:
	if proposal is None:
		strict_contract = _validate_strict_deterministic_safe_subset(raw_message, strict_deterministic_safe_subset)
		if strict_contract is not None:
			return strict_contract
		return _invalid_contract(raw_message, ["intent_proposal_missing"])

	proposal_mapping = _coerce_mapping(proposal)
	if proposal_mapping is None:
		return _invalid_contract(raw_message, ["intent_proposal_not_object"])

	normalized = normalize_message(raw_message)
	errors = _missing_fields(proposal_mapping, REQUIRED_PROPOSAL_FIELDS)
	errors.extend(_proposal_metadata_errors(proposal_mapping))
	lexical_conservative_alarm = bool(proposal_mapping.get("lexical_conservative_alarm"))
	lexical_alarm_reason = str(proposal_mapping.get("lexical_alarm_reason") or "")
	lexical_authority_effect = (
		LEXICAL_AUTHORITY_EFFECT_RESTRICT_ONLY
		if lexical_conservative_alarm
		else LEXICAL_AUTHORITY_EFFECT_NONE
	)
	validator_mechanical_status, validator_mechanical_command_id = _validator_owned_mechanical_status(
		proposal_mapping.get("mechanical_command_id")
	)
	if lexical_conservative_alarm:
		errors.append("lexical_conservative_alarm_restricts_routing")

	semantic_status, semantic_effect, semantic_error = _semantic_backstop(semantic_backstop)
	if semantic_error:
		errors.append(semantic_error)

	targets = _validate_targets(proposal_mapping.get("erp_targets"), errors)
	target_ids = {target["target_id"] for target in targets}
	references = _validate_references(proposal_mapping.get("visible_context_references"), target_ids, errors)
	reference_ids = {reference["reference_id"] for reference in references}
	clauses = _validate_clauses(proposal_mapping.get("clauses"), normalized, target_ids, reference_ids, errors)
	errors.extend(_proposal_completeness_errors(proposal_mapping, clauses, normalized))
	role_verification_errors, role_metadata, verified_by_clause_id = _validate_clause_role_verification(
		proposal_mapping,
		clauses,
		raw_message,
		normalized,
		verifier_envelope,
		trusted_verifier_registry,
	)
	errors.extend(role_verification_errors)
	role_verification_blocking_reason = str(role_metadata.get("role_verification_blocking_reason") or "")
	natural_language_report_authority_status = str(role_metadata.get("natural_language_report_authority_status") or "")

	if isinstance(proposal_mapping.get("clause_count"), int):
		if proposal_mapping["clause_count"] != len(clauses):
			errors.append("clause_count_mismatch")
	else:
		errors.append("clause_count_not_integer")

	residual_segments = _compute_residual_segments(normalized, clauses) if clauses else []
	if residual_segments:
		errors.append("unresolved_residual_text")

	pronoun_reference_status = "complete"
	if any(reference.get("resolution_status") == REFERENCE_UNRESOLVED for reference in references):
		pronoun_reference_status = "unresolved"

	connector_coverage_status = "complete" if not residual_segments else "unresolved"
	aggregates = _aggregate_contract_intents(clauses)

	if aggregates["business_action_intent"] and proposal_mapping.get("mixed_intent_detected") is False and aggregates["factual_lookup_intent"]:
		errors.append("contradictory_mixed_intent_flag")
	if proposal_mapping.get("mixed_intent_detected") is True and not aggregates["business_action_intent"]:
		errors.append("mixed_intent_without_unsafe_clause")

	safety_proof_errors, safety_proof_metadata = _validate_validator_owned_safety_proof(
		raw_message,
		clauses,
		targets,
		references,
		residual_segments,
		connector_coverage_status,
		pronoun_reference_status,
		semantic_status,
		lexical_conservative_alarm,
		aggregates,
		proposal_mapping,
		role_metadata,
		validator_owned_safety_proof_registry,
	)
	errors.extend(safety_proof_errors)

	if errors:
		return _invalid_contract(
			raw_message,
			errors,
			intent_proposer_role=str(proposal_mapping.get("intent_proposer_role") or ""),
			intent_proposer_status=str(proposal_mapping.get("intent_proposer_status") or ""),
			intent_proposer_confidence=float(proposal_mapping.get("intent_proposer_confidence") or 0.0),
			intent_proposer_model_name=str(proposal_mapping.get("intent_proposer_model_name") or ""),
			intent_proposer_output_status=str(proposal_mapping.get("intent_proposer_output_status") or ""),
			proposal_authority_source=str(proposal_mapping.get("proposal_authority_source") or ""),
			proposal_completeness_status=str(proposal_mapping.get("proposal_completeness_status") or ""),
			clause_segmentation_status=str(proposal_mapping.get("clause_segmentation_status") or ""),
			secondary_intent_audit_status=str(proposal_mapping.get("secondary_intent_audit_status") or ""),
			residual_audit_status=str(proposal_mapping.get("residual_audit_status") or ""),
			clause_role_confidence_status=str(proposal_mapping.get("clause_role_confidence_status") or ""),
			full_span_factual_authority=str(proposal_mapping.get("full_span_factual_authority") or ""),
			full_span_factual_allow_reason=str(proposal_mapping.get("full_span_factual_allow_reason") or ""),
			natural_language_interpretation_required=bool(proposal_mapping.get("natural_language_interpretation_required", True)),
			independent_parse_guard_status=str(proposal_mapping.get("independent_parse_guard_status") or ""),
			lexical_authority_effect=lexical_authority_effect,
			lexical_conservative_alarm=lexical_conservative_alarm,
			lexical_alarm_reason=lexical_alarm_reason,
			validator_owned_mechanical_authority_status=validator_mechanical_status,
			validator_owned_mechanical_command_id=validator_mechanical_command_id,
			clause_role_verification_required=bool(role_metadata.get("clause_role_verification_required")),
			clause_role_verifier_source=str(role_metadata.get("clause_role_verifier_source") or ""),
			clause_role_verifier_run_id=str(role_metadata.get("clause_role_verifier_run_id") or ""),
			clause_role_verifier_model_name=str(role_metadata.get("clause_role_verifier_model_name") or ""),
			clause_role_verifier_prompt_version=str(role_metadata.get("clause_role_verifier_prompt_version") or ""),
			clause_role_verifier_payload_hash=str(role_metadata.get("clause_role_verifier_payload_hash") or ""),
			clause_role_verifier_status=str(role_metadata.get("clause_role_verifier_status") or ""),
			clause_role_verifier_independence_status=str(role_metadata.get("clause_role_verifier_independence_status") or ""),
			clause_role_verifier_authority_effect=str(role_metadata.get("clause_role_verifier_authority_effect") or ""),
			clause_role_verifier_provenance_status=str(role_metadata.get("clause_role_verifier_provenance_status") or VERIFIER_PROVENANCE_UNTRUSTED),
			clause_role_verifier_payload_hash_status=str(role_metadata.get("clause_role_verifier_payload_hash_status") or VERIFIER_PAYLOAD_HASH_FAILED),
			clause_role_verifier_attestation_status=str(role_metadata.get("clause_role_verifier_attestation_status") or VERIFIER_ATTESTATION_FAILED),
			all_clause_roles_verified=bool(role_metadata.get("all_clause_roles_verified")),
			proposer_verifier_agreement_status=str(role_metadata.get("proposer_verifier_agreement_status") or ""),
			role_disagreement_policy=str(role_metadata.get("role_disagreement_policy") or ""),
			role_verification_blocking_reason=role_verification_blocking_reason,
			natural_language_report_authority_status=natural_language_report_authority_status,
			validator_owned_safety_proof_required=bool(safety_proof_metadata.get("validator_owned_safety_proof_required", True)),
			validator_owned_safety_proof_status=str(safety_proof_metadata.get("validator_owned_safety_proof_status") or "failed"),
			validator_owned_safety_proof_source=str(safety_proof_metadata.get("validator_owned_safety_proof_source") or VALIDATOR_OWNED_SAFETY_PROOF_SOURCE),
			validator_owned_safety_proof_version=str(safety_proof_metadata.get("validator_owned_safety_proof_version") or VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_PROOF_VERSION),
			validator_owned_safety_proof_blocking_reason=str(safety_proof_metadata.get("validator_owned_safety_proof_blocking_reason") or ""),
			validator_owned_safe_route_authority_status=str(safety_proof_metadata.get("validator_owned_safe_route_authority_status") or VALIDATOR_SAFE_ROUTE_BLOCKED_WITHOUT_PROOF),
			validator_owned_safety_analyzer_id=str(safety_proof_metadata.get("validator_owned_safety_analyzer_id") or ""),
			validator_owned_safety_analyzer_version=str(safety_proof_metadata.get("validator_owned_safety_analyzer_version") or ""),
			validator_owned_raw_message_safety_status=str(safety_proof_metadata.get("validator_owned_raw_message_safety_status") or ""),
			validator_owned_raw_message_clause_coverage_status=str(safety_proof_metadata.get("validator_owned_raw_message_clause_coverage_status") or ""),
			validator_owned_raw_message_secondary_intent_status=str(safety_proof_metadata.get("validator_owned_raw_message_secondary_intent_status") or ""),
			validator_owned_raw_message_mixed_intent_status=str(safety_proof_metadata.get("validator_owned_raw_message_mixed_intent_status") or ""),
			validator_owned_raw_message_residual_status=str(safety_proof_metadata.get("validator_owned_raw_message_residual_status") or ""),
			validator_owned_raw_message_reference_status=str(safety_proof_metadata.get("validator_owned_raw_message_reference_status") or ""),
			validator_owned_safety_proof_basis=str(safety_proof_metadata.get("validator_owned_safety_proof_basis") or ""),
			validator_owned_safety_proof_attestation_status=str(safety_proof_metadata.get("validator_owned_safety_proof_attestation_status") or SAFETY_PROOF_ATTESTATION_FAILED),
			validator_owned_safety_proof_id=str(safety_proof_metadata.get("validator_owned_safety_proof_id") or ""),
			validator_owned_safety_proof_subject_hash=str(safety_proof_metadata.get("validator_owned_safety_proof_subject_hash") or ""),
			validator_owned_safety_proof_uniqueness_status=str(safety_proof_metadata.get("validator_owned_safety_proof_uniqueness_status") or ""),
			validator_owned_safety_proof_conflict_status=str(safety_proof_metadata.get("validator_owned_safety_proof_conflict_status") or ""),
			validator_owned_safety_proof_evidence_status=str(safety_proof_metadata.get("validator_owned_safety_proof_evidence_status") or ""),
			validator_owned_safety_proof_evidence_semantics_status=str(
				safety_proof_metadata.get("validator_owned_safety_proof_evidence_semantics_status") or ""
			),
			validator_owned_raw_message_analysis_required=bool(
				safety_proof_metadata.get("validator_owned_raw_message_analysis_required", True)
			),
			validator_owned_raw_message_analysis_status=str(
				safety_proof_metadata.get("validator_owned_raw_message_analysis_status") or ""
			),
			validator_owned_raw_message_analysis_source=str(
				safety_proof_metadata.get("validator_owned_raw_message_analysis_source") or VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_SOURCE
			),
			validator_owned_raw_message_analysis_version=str(
				safety_proof_metadata.get("validator_owned_raw_message_analysis_version") or VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_VERSION
			),
			validator_owned_raw_message_analysis_subject_hash=str(
				safety_proof_metadata.get("validator_owned_raw_message_analysis_subject_hash") or ""
			),
			validator_owned_raw_message_analysis_evidence_match_status=str(
				safety_proof_metadata.get("validator_owned_raw_message_analysis_evidence_match_status") or ""
			),
			validator_owned_raw_message_analysis_blocking_reason=str(
				safety_proof_metadata.get("validator_owned_raw_message_analysis_blocking_reason") or ""
			),
			analysis_execution_required=bool(safety_proof_metadata.get("analysis_execution_required", True)),
			analysis_execution_status=str(safety_proof_metadata.get("analysis_execution_status") or ""),
			analysis_execution_source=str(
				safety_proof_metadata.get("analysis_execution_source")
				or VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_SOURCE
			),
			analysis_execution_version=str(
				safety_proof_metadata.get("analysis_execution_version")
				or VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_VERSION
			),
			analysis_execution_run_id=str(safety_proof_metadata.get("analysis_execution_run_id") or ""),
			analysis_execution_subject_hash=str(safety_proof_metadata.get("analysis_execution_subject_hash") or ""),
			analysis_execution_input_hash=str(safety_proof_metadata.get("analysis_execution_input_hash") or ""),
			analysis_execution_output_hash=str(safety_proof_metadata.get("analysis_execution_output_hash") or ""),
			analysis_execution_artifact_hash=str(safety_proof_metadata.get("analysis_execution_artifact_hash") or ""),
			analysis_execution_replay_status=str(safety_proof_metadata.get("analysis_execution_replay_status") or ""),
			analysis_execution_blocking_reason=str(safety_proof_metadata.get("analysis_execution_blocking_reason") or ""),
			replayed_raw_message_safety_required=bool(safety_proof_metadata.get("replayed_raw_message_safety_required", True)),
			replayed_raw_message_safety_status=str(safety_proof_metadata.get("replayed_raw_message_safety_status") or ""),
			replayed_raw_message_safety_source=str(
				safety_proof_metadata.get("replayed_raw_message_safety_source")
				or VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_SOURCE
			),
			replayed_raw_message_safety_version=str(
				safety_proof_metadata.get("replayed_raw_message_safety_version")
				or VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_VERSION
			),
			replayed_raw_message_safety_config_hash=str(
				safety_proof_metadata.get("replayed_raw_message_safety_config_hash") or ""
			),
			replayed_raw_message_safety_subject_hash=str(
				safety_proof_metadata.get("replayed_raw_message_safety_subject_hash") or ""
			),
			replayed_raw_message_safety_final_decision=str(
				safety_proof_metadata.get("replayed_raw_message_safety_final_decision") or ""
			),
			replayed_raw_message_safety_evidence_match_status=str(
				safety_proof_metadata.get("replayed_raw_message_safety_evidence_match_status") or ""
			),
			replayed_raw_message_safety_blocking_reason=str(
				safety_proof_metadata.get("replayed_raw_message_safety_blocking_reason") or ""
			),
			role_verification_authority_effect=str(safety_proof_metadata.get("role_verification_authority_effect") or ROLE_VERIFICATION_AUTHORITY_EFFECT_CONSISTENCY_ONLY),
			semantic_backstop_authority_effect=str(safety_proof_metadata.get("semantic_backstop_authority_effect") or SEMANTIC_BACKSTOP_AUTHORITY_EFFECT_RESTRICT_ONLY),
			lexical_evidence_authority_effect=str(safety_proof_metadata.get("lexical_evidence_authority_effect") or LEXICAL_EVIDENCE_AUTHORITY_EFFECT_RESTRICT_ONLY),
			semantic_backstop_status=semantic_status,
			semantic_backstop_effect=semantic_effect,
			residual_segments=residual_segments,
			trace_redaction_status=str(proposal_mapping.get("trace_redaction_status") or "unknown"),
			pronoun_reference_status=pronoun_reference_status,
			connector_coverage_status=connector_coverage_status,
		)

	semantic_restricts = semantic_status in {SEMANTIC_BACKSTOP_UNSAFE, SEMANTIC_BACKSTOP_AMBIGUOUS}
	unsafe_intent = (
		aggregates["decision_intent"]
		or aggregates["advice_intent"]
		or aggregates["business_action_intent"]
		or aggregates["policy_boundary_intent"]
		or aggregates["business_action_domain"] != DOMAIN_NONE
		or aggregates["policy_domain"] != DOMAIN_NONE
	)
	ambiguous = aggregates["ambiguity_status"] != "none"
	report_allowed = bool(aggregates["factual_lookup_intent"] and not unsafe_intent and not ambiguous and not semantic_restricts)
	context_allowed = bool(aggregates["safe_followup_intent"] and not unsafe_intent and not ambiguous and not semantic_restricts)
	if semantic_restricts:
		answer_mode = ANSWER_MODE_CLARIFICATION
		authority_decision = AUTHORITY_DECISION_CLARIFICATION
		boundary_reason = "semantic_backstop_restricted_routing"
	elif unsafe_intent:
		answer_mode = _answer_mode_for_domain(aggregates["business_action_domain"], aggregates["ambiguity_status"])
		authority_decision = AUTHORITY_DECISION_BOUNDARY if answer_mode != ANSWER_MODE_CLARIFICATION else AUTHORITY_DECISION_CLARIFICATION
		boundary_reason = "unsafe_or_mixed_intent_requires_boundary"
	elif ambiguous:
		answer_mode = ANSWER_MODE_CLARIFICATION
		authority_decision = AUTHORITY_DECISION_CLARIFICATION
		boundary_reason = "ambiguity_requires_clarification"
	else:
		answer_mode = ANSWER_MODE_GOVERNED_ERP
		authority_decision = AUTHORITY_DECISION_ALLOW_REPORT
		boundary_reason = "validated_safe_factual_intent"

	model_reasoning_allowed = bool(report_allowed and answer_mode == ANSWER_MODE_GOVERNED_ERP)
	final_emission_allowed = True

	return IntentBoundaryContract(
		contract_version=CONTRACT_VERSION,
		raw_message_hash=hash_text(raw_message),
		normalized_message_hash=hash_text(normalized),
		clause_count=len(clauses),
		clauses=[_redact_clause(clause) for clause in _clauses_with_external_verification(clauses, verified_by_clause_id)],
		erp_targets=[_redact_target(target) for target in targets],
		visible_context_references=[_reference_payload(reference) for reference in references],
		factual_lookup_intent=aggregates["factual_lookup_intent"],
		safe_followup_intent=aggregates["safe_followup_intent"],
		decision_intent=aggregates["decision_intent"],
		advice_intent=aggregates["advice_intent"],
		business_action_intent=aggregates["business_action_intent"],
		policy_boundary_intent=aggregates["policy_boundary_intent"],
		mixed_intent_detected=bool(proposal_mapping.get("mixed_intent_detected")),
		business_action_domain=aggregates["business_action_domain"],
		policy_domain=aggregates["policy_domain"],
		ambiguity_status=aggregates["ambiguity_status"],
		report_routing_allowed=report_allowed,
		context_reuse_allowed=context_allowed,
		model_reasoning_allowed=model_reasoning_allowed,
		final_emission_allowed=final_emission_allowed,
		required_answer_mode=answer_mode,
		boundary_reason=boundary_reason,
		validator_status=DETERMINISTIC_VALIDATOR_VALID,
		trace_redaction_status=TRACE_REDACTION_SAFE,
		intent_proposer_role=str(proposal_mapping["intent_proposer_role"]),
		intent_proposer_status=str(proposal_mapping["intent_proposer_status"]),
		intent_proposer_confidence=float(proposal_mapping["intent_proposer_confidence"]),
		intent_proposer_model_name=str(proposal_mapping["intent_proposer_model_name"]),
		intent_proposer_output_status=str(proposal_mapping["intent_proposer_output_status"]),
		proposal_authority_source=str(proposal_mapping["proposal_authority_source"]),
		proposal_completeness_status=str(proposal_mapping["proposal_completeness_status"]),
		clause_segmentation_status=str(proposal_mapping["clause_segmentation_status"]),
		secondary_intent_audit_status=str(proposal_mapping["secondary_intent_audit_status"]),
		residual_audit_status=str(proposal_mapping["residual_audit_status"]),
		clause_role_confidence_status=str(proposal_mapping["clause_role_confidence_status"]),
		full_span_factual_authority=str(proposal_mapping["full_span_factual_authority"]),
		full_span_factual_allow_reason=str(proposal_mapping["full_span_factual_allow_reason"]),
		natural_language_interpretation_required=bool(proposal_mapping["natural_language_interpretation_required"]),
		independent_parse_guard_status=str(proposal_mapping["independent_parse_guard_status"]),
		lexical_authority_effect=lexical_authority_effect,
		lexical_conservative_alarm=lexical_conservative_alarm,
		lexical_alarm_reason=lexical_alarm_reason,
		validator_owned_mechanical_authority_status=validator_mechanical_status,
		validator_owned_mechanical_command_id=validator_mechanical_command_id,
		clause_role_verification_required=bool(role_metadata.get("clause_role_verification_required")),
		clause_role_verifier_source=str(role_metadata.get("clause_role_verifier_source") or ""),
		clause_role_verifier_run_id=str(role_metadata.get("clause_role_verifier_run_id") or ""),
		clause_role_verifier_model_name=str(role_metadata.get("clause_role_verifier_model_name") or ""),
		clause_role_verifier_prompt_version=str(role_metadata.get("clause_role_verifier_prompt_version") or ""),
		clause_role_verifier_payload_hash=str(role_metadata.get("clause_role_verifier_payload_hash") or ""),
		clause_role_verifier_status=str(role_metadata.get("clause_role_verifier_status") or ""),
		clause_role_verifier_independence_status=str(role_metadata.get("clause_role_verifier_independence_status") or ""),
		clause_role_verifier_authority_effect=str(role_metadata.get("clause_role_verifier_authority_effect") or ""),
		clause_role_verifier_provenance_status=str(role_metadata.get("clause_role_verifier_provenance_status") or VERIFIER_PROVENANCE_UNTRUSTED),
		clause_role_verifier_payload_hash_status=str(role_metadata.get("clause_role_verifier_payload_hash_status") or VERIFIER_PAYLOAD_HASH_FAILED),
		clause_role_verifier_attestation_status=str(role_metadata.get("clause_role_verifier_attestation_status") or VERIFIER_ATTESTATION_FAILED),
		all_clause_roles_verified=bool(role_metadata.get("all_clause_roles_verified")),
		proposer_verifier_agreement_status=str(role_metadata.get("proposer_verifier_agreement_status") or ""),
		role_disagreement_policy=str(role_metadata.get("role_disagreement_policy") or ""),
		role_verification_blocking_reason=role_verification_blocking_reason,
		natural_language_report_authority_status=natural_language_report_authority_status,
		validator_owned_safety_proof_required=bool(safety_proof_metadata.get("validator_owned_safety_proof_required", True)),
		validator_owned_safety_proof_status=str(safety_proof_metadata.get("validator_owned_safety_proof_status") or ""),
		validator_owned_safety_proof_source=str(safety_proof_metadata.get("validator_owned_safety_proof_source") or VALIDATOR_OWNED_SAFETY_PROOF_SOURCE),
		validator_owned_safety_proof_version=str(safety_proof_metadata.get("validator_owned_safety_proof_version") or VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_PROOF_VERSION),
		validator_owned_safety_proof_blocking_reason=str(safety_proof_metadata.get("validator_owned_safety_proof_blocking_reason") or ""),
		validator_owned_safe_route_authority_status=str(safety_proof_metadata.get("validator_owned_safe_route_authority_status") or VALIDATOR_SAFE_ROUTE_BLOCKED_WITHOUT_PROOF),
		validator_owned_safety_analyzer_id=str(safety_proof_metadata.get("validator_owned_safety_analyzer_id") or ""),
		validator_owned_safety_analyzer_version=str(safety_proof_metadata.get("validator_owned_safety_analyzer_version") or ""),
		validator_owned_raw_message_safety_status=str(safety_proof_metadata.get("validator_owned_raw_message_safety_status") or ""),
		validator_owned_raw_message_clause_coverage_status=str(safety_proof_metadata.get("validator_owned_raw_message_clause_coverage_status") or ""),
		validator_owned_raw_message_secondary_intent_status=str(safety_proof_metadata.get("validator_owned_raw_message_secondary_intent_status") or ""),
		validator_owned_raw_message_mixed_intent_status=str(safety_proof_metadata.get("validator_owned_raw_message_mixed_intent_status") or ""),
		validator_owned_raw_message_residual_status=str(safety_proof_metadata.get("validator_owned_raw_message_residual_status") or ""),
		validator_owned_raw_message_reference_status=str(safety_proof_metadata.get("validator_owned_raw_message_reference_status") or ""),
		validator_owned_safety_proof_basis=str(safety_proof_metadata.get("validator_owned_safety_proof_basis") or ""),
		validator_owned_safety_proof_attestation_status=str(safety_proof_metadata.get("validator_owned_safety_proof_attestation_status") or SAFETY_PROOF_ATTESTATION_FAILED),
		validator_owned_safety_proof_id=str(safety_proof_metadata.get("validator_owned_safety_proof_id") or ""),
		validator_owned_safety_proof_subject_hash=str(safety_proof_metadata.get("validator_owned_safety_proof_subject_hash") or ""),
		validator_owned_safety_proof_uniqueness_status=str(safety_proof_metadata.get("validator_owned_safety_proof_uniqueness_status") or ""),
		validator_owned_safety_proof_conflict_status=str(safety_proof_metadata.get("validator_owned_safety_proof_conflict_status") or ""),
		validator_owned_safety_proof_evidence_status=str(safety_proof_metadata.get("validator_owned_safety_proof_evidence_status") or ""),
		validator_owned_safety_proof_evidence_semantics_status=str(
			safety_proof_metadata.get("validator_owned_safety_proof_evidence_semantics_status") or ""
		),
		validator_owned_raw_message_analysis_required=bool(
			safety_proof_metadata.get("validator_owned_raw_message_analysis_required", True)
		),
		validator_owned_raw_message_analysis_status=str(
			safety_proof_metadata.get("validator_owned_raw_message_analysis_status") or ""
		),
		validator_owned_raw_message_analysis_source=str(
			safety_proof_metadata.get("validator_owned_raw_message_analysis_source") or VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_SOURCE
		),
		validator_owned_raw_message_analysis_version=str(
			safety_proof_metadata.get("validator_owned_raw_message_analysis_version") or VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_VERSION
		),
		validator_owned_raw_message_analysis_subject_hash=str(
			safety_proof_metadata.get("validator_owned_raw_message_analysis_subject_hash") or ""
		),
		validator_owned_raw_message_analysis_evidence_match_status=str(
			safety_proof_metadata.get("validator_owned_raw_message_analysis_evidence_match_status") or ""
		),
		validator_owned_raw_message_analysis_blocking_reason=str(
			safety_proof_metadata.get("validator_owned_raw_message_analysis_blocking_reason") or ""
		),
		analysis_execution_required=bool(safety_proof_metadata.get("analysis_execution_required", True)),
		analysis_execution_status=str(safety_proof_metadata.get("analysis_execution_status") or ""),
		analysis_execution_source=str(
			safety_proof_metadata.get("analysis_execution_source")
			or VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_SOURCE
		),
		analysis_execution_version=str(
			safety_proof_metadata.get("analysis_execution_version")
			or VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_VERSION
		),
		analysis_execution_run_id=str(safety_proof_metadata.get("analysis_execution_run_id") or ""),
		analysis_execution_subject_hash=str(safety_proof_metadata.get("analysis_execution_subject_hash") or ""),
		analysis_execution_input_hash=str(safety_proof_metadata.get("analysis_execution_input_hash") or ""),
		analysis_execution_output_hash=str(safety_proof_metadata.get("analysis_execution_output_hash") or ""),
		analysis_execution_artifact_hash=str(safety_proof_metadata.get("analysis_execution_artifact_hash") or ""),
		analysis_execution_replay_status=str(safety_proof_metadata.get("analysis_execution_replay_status") or ""),
		analysis_execution_blocking_reason=str(safety_proof_metadata.get("analysis_execution_blocking_reason") or ""),
		replayed_raw_message_safety_required=bool(safety_proof_metadata.get("replayed_raw_message_safety_required", True)),
		replayed_raw_message_safety_status=str(safety_proof_metadata.get("replayed_raw_message_safety_status") or ""),
		replayed_raw_message_safety_source=str(
			safety_proof_metadata.get("replayed_raw_message_safety_source")
			or VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_SOURCE
		),
		replayed_raw_message_safety_version=str(
			safety_proof_metadata.get("replayed_raw_message_safety_version")
			or VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_VERSION
		),
		replayed_raw_message_safety_config_hash=str(safety_proof_metadata.get("replayed_raw_message_safety_config_hash") or ""),
		replayed_raw_message_safety_subject_hash=str(safety_proof_metadata.get("replayed_raw_message_safety_subject_hash") or ""),
		replayed_raw_message_safety_final_decision=str(
			safety_proof_metadata.get("replayed_raw_message_safety_final_decision") or ""
		),
		replayed_raw_message_safety_evidence_match_status=str(
			safety_proof_metadata.get("replayed_raw_message_safety_evidence_match_status") or ""
		),
		replayed_raw_message_safety_blocking_reason=str(
			safety_proof_metadata.get("replayed_raw_message_safety_blocking_reason") or ""
		),
		role_verification_authority_effect=str(safety_proof_metadata.get("role_verification_authority_effect") or ROLE_VERIFICATION_AUTHORITY_EFFECT_CONSISTENCY_ONLY),
		semantic_backstop_authority_effect=str(safety_proof_metadata.get("semantic_backstop_authority_effect") or SEMANTIC_BACKSTOP_AUTHORITY_EFFECT_RESTRICT_ONLY),
		lexical_evidence_authority_effect=str(safety_proof_metadata.get("lexical_evidence_authority_effect") or LEXICAL_EVIDENCE_AUTHORITY_EFFECT_RESTRICT_ONLY),
		deterministic_validator_status=DETERMINISTIC_VALIDATOR_VALID,
		deterministic_validator_errors=[],
		semantic_backstop_status=semantic_status,
		semantic_backstop_effect=semantic_effect,
		authority_source=AUTHORITY_SOURCE_DETERMINISTIC_VALIDATOR,
		authority_decision=authority_decision,
		authority_blocking_reason="" if authority_decision == AUTHORITY_DECISION_ALLOW_REPORT else boundary_reason,
		residual_text_status="accounted",
		residual_text_segments=[],
		connector_coverage_status=connector_coverage_status,
		pronoun_reference_status=pronoun_reference_status,
	)


def strict_deterministic_safe_subset_definition() -> Dict[str, Any]:
	return {
		"name": "strict_deterministic_safe_subset",
		"authority_model": "mechanical_only_no_semantic_or_lexical_authority",
		"validator_owned_mechanical_registry_count": len(VALIDATOR_OWNED_MECHANICAL_COMMAND_REGISTRY),
		"allow_condition": (
			"Only pre-approved mechanical command shapes may use this path; "
			"self-attested semantic safety flags cannot authorize ERP report routing."
		),
		"requirements": {
			"decision_intent": False,
			"advice_intent": False,
			"business_action_intent": False,
			"policy_boundary_intent": False,
			"legal_or_regulatory_advice_intent": False,
			"prediction_score_or_future_cause_intent": False,
			"manipulation_report_hiding_intent": False,
			"write_mutation_workflow_intent": False,
			"unsupported_business_recommendation_intent": False,
			"unresolved_residual_clause": False,
			"mixed_intent_detected": False,
			"visible_context_ambiguity": False,
			"unresolved_pronoun_or_reference": False,
			"unsafe_domain_evidence": False,
			"target_schema_status": "valid",
			"clause_coverage_status": "complete",
			"contract_invariants_status": "valid",
			"trace_redaction_status": TRACE_REDACTION_SAFE,
			"natural_language_interpretation_required": False,
			"mechanical_command_id": "required",
			"mechanical_command_registry_status": "approved",
			"intent_interpretation_required": False,
		},
	}
