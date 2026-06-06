import unittest

from ai_assistant_ui.qwen_chat import intent_boundary_contract as ibc
from ai_assistant_ui.qwen_chat.intent_boundary_contract import (
	ANSWER_MODE_CLARIFICATION,
	ANSWER_MODE_GOVERNED_ERP,
	AUDIT_STATUS_PASSED,
	AUTHORITY_DECISION_ALLOW_REPORT,
	AUTHORITY_DECISION_BLOCK,
	CLAUSE_TYPE_BUSINESS_ACTION,
	CLAUSE_TYPE_FACTUAL_LOOKUP,
	COMPLETENESS_STATUS_COMPLETE,
	DOMAIN_NONE,
	DOMAIN_LEGAL_OR_REGULATORY_ADVICE,
	DOMAIN_PRICING_VALUATION_ACTION,
	FULL_SPAN_FACTUAL_AUTHORITY_NOT_ALLOWED,
	LEXICAL_AUTHORITY_EFFECT_RESTRICT_ONLY,
	NATURAL_LANGUAGE_REPORT_AUTHORITY_VERIFIED,
	PROPOSAL_SOURCE_DETERMINISTIC_SAFE_SUBSET,
	PROPOSAL_SOURCE_LIGHTWEIGHT_MODEL,
	PROPOSER_OUTPUT_VALID,
	PROPOSER_ROLE_LIGHTWEIGHT,
	PROPOSER_STATUS_COMPLETE,
	ROLE_DISAGREEMENT_POLICY_FAIL_CLOSED,
	SEMANTIC_BACKSTOP_AMBIGUOUS,
	SEMANTIC_BACKSTOP_SAFE,
	SEMANTIC_BACKSTOP_UNSAFE,
	TARGET_TYPE_CUSTOMER,
	TARGET_TYPE_INVOICE,
	TARGET_TYPE_ITEM,
	TARGET_TYPE_SUPPLIER,
	TRACE_REDACTION_SAFE,
	VERIFIER_AUTHORITY_EFFECT_CONSISTENCY_ONLY,
	VERIFIER_ATTESTATION_FAILED,
	VERIFIER_ATTESTATION_VERIFIED,
	VERIFIER_PAYLOAD_HASH_MATCHED,
	VERIFIER_PROVENANCE_TRUSTED,
	VALIDATOR_OWNED_SAFETY_PROOF_SOURCE,
	VALIDATOR_OWNED_SAFETY_PROOF_VERSION,
	VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_SOURCE,
	VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_PROOF_VERSION,
	VALIDATOR_SAFE_ROUTE_BLOCKED_WITHOUT_PROOF,
	VALIDATOR_SAFE_ROUTE_PROVEN,
	RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE,
	canonical_raw_message_safety_proof_payload,
	canonical_verifier_payload_hash,
	detect_raw_message_unsafe_evidence,
	hash_text,
	normalize_message,
	raw_message_safety_proof_attestation_hash,
	raw_message_safety_evidence_hash,
	raw_message_safety_proof_payload_hash,
	raw_message_safety_proof_subject_hash,
	strict_deterministic_safe_subset_definition,
	validate_intent_boundary_contract,
	validator_owned_safety_proof_id,
	verifier_attestation_hash,
)


class V1IBIntentBoundaryContractValidatorTests(unittest.TestCase):
	TRUSTED_VERIFIER_SOURCE = "trusted_clause_role_guard"
	TRUSTED_VERIFIER_MODEL = "trusted-test-verifier"
	TRUSTED_VERIFIER_PROMPT_VERSION = "v1-ib-a-i-test"
	TRUSTED_VERIFIER_SECRET = "v1-ib-a-i-test-secret"
	TRUSTED_ANALYZER_ID = "validator-owned-raw-message-analyzer"
	TRUSTED_ANALYZER_VERSION = "v1-ib-a-k-test"
	TRUSTED_ANALYZER_SECRET = "v1-ib-a-k-test-secret"

	def setUp(self):
		self.clear_raw_message_safety_proofs()

	def tearDown(self):
		self.clear_raw_message_safety_proofs()

	def trusted_verifier_registry(self):
		return {
			self.TRUSTED_VERIFIER_SOURCE: {
				"registry_status": "approved",
				"approved_prompt_versions": [self.TRUSTED_VERIFIER_PROMPT_VERSION],
				"allowed_model_names": [self.TRUSTED_VERIFIER_MODEL],
				"attestation_secret": self.TRUSTED_VERIFIER_SECRET,
				"test_only": True,
			}
		}

	def raw_message_safety_analyzer_registry(self):
		return {
			self.TRUSTED_ANALYZER_ID: {
				"registry_status": "approved",
				"approved_analyzer_versions": [self.TRUSTED_ANALYZER_VERSION],
				"attestation_secret": self.TRUSTED_ANALYZER_SECRET,
				"replay_source": ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_SOURCE,
				"replay_version": ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_VERSION,
				"replay_config_hash": hash_text("v1-ib-a-p-test-replay-config"),
				"replay_artifact_hash": hash_text("v1-ib-a-p-test-replay-artifact"),
				"test_only": True,
			}
		}

	def raw_message_analysis(self, message, proof, **overrides):
		raw_hash = hash_text(message)
		normalized_hash = hash_text(normalize_message(message))
		subject_hash = raw_message_safety_proof_subject_hash(raw_hash, normalized_hash)
		analysis = {
			"registry_status": "approved",
			"raw_message_hash": raw_hash,
			"normalized_message_hash": normalized_hash,
			"raw_message_analysis_subject_hash": subject_hash,
			"analysis_source": ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_SOURCE,
			"analysis_version": ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_VERSION,
			"analysis_status": "safe",
			"validator_safety_analyzer_id": self.TRUSTED_ANALYZER_ID,
			"validator_safety_analyzer_version": self.TRUSTED_ANALYZER_VERSION,
			"raw_message_clause_coverage_status": proof.get("raw_message_clause_coverage_status"),
			"raw_message_secondary_intent_status": proof.get("raw_message_secondary_intent_status"),
			"raw_message_mixed_intent_status": proof.get("raw_message_mixed_intent_status"),
			"raw_message_residual_status": proof.get("raw_message_residual_status"),
			"raw_message_connector_status": "accounted",
			"raw_message_reference_status": proof.get("raw_message_reference_status"),
			"raw_message_unsafe_ambiguity_status": "none",
			"analysis_basis": RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE,
			"derived_from_proposer_roles": False,
			"derived_from_verifier_roles": False,
			"derived_from_semantic_safe_output": False,
			"derived_from_lexical_phrase_authority": False,
			"trace_redaction_status": TRACE_REDACTION_SAFE,
		}
		analysis.update(self.analysis_evidence_hashes(proof))
		analysis.update(overrides)
		return analysis

	def raw_message_analysis_execution(self, message, analysis, **overrides):
		raw_hash = hash_text(message)
		normalized_hash = hash_text(normalize_message(message))
		subject_hash = raw_message_safety_proof_subject_hash(raw_hash, normalized_hash)
		execution = {
			"registry_status": "approved",
			"raw_message_hash": raw_hash,
			"normalized_message_hash": normalized_hash,
			"analyzer_id": self.TRUSTED_ANALYZER_ID,
			"analyzer_version": self.TRUSTED_ANALYZER_VERSION,
			"run_id": f"analysis-run-{subject_hash[:12]}",
			"input_hash": ibc.raw_message_analysis_input_hash(raw_hash, normalized_hash, subject_hash),
			"output_hash": ibc.raw_message_analysis_output_hash(analysis),
			"artifact_hash": hash_text(f"analysis-artifact:{subject_hash}"),
			"execution_source": ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_SOURCE,
			"execution_version": ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_VERSION,
			"execution_mode": "validator_owned_test_fixture",
			"execution_status": "completed",
			"trace_redaction_status": TRACE_REDACTION_SAFE,
			"replay_status": "verified",
		}
		deferred = {
			key: overrides.pop(key)
			for key in list(overrides)
			if key in {"execution_payload_hash", "attestation"}
		}
		execution.update(overrides)
		execution["execution_payload_hash"] = ibc.raw_message_analysis_execution_payload_hash(execution)
		execution["attestation"] = ibc.raw_message_analysis_execution_attestation_hash(
			self.TRUSTED_ANALYZER_SECRET,
			execution["execution_payload_hash"],
		)
		execution.update(deferred)
		return execution

	def analysis_evidence_hashes(self, proof):
		return {
			"raw_message_clause_coverage_evidence_hash": proof["raw_message_clause_coverage_evidence"]["evidence_hash"],
			"raw_message_secondary_intent_evidence_hash": proof["raw_message_secondary_intent_evidence"]["evidence_hash"],
			"raw_message_mixed_intent_evidence_hash": proof["raw_message_mixed_intent_evidence"]["evidence_hash"],
			"raw_message_residual_evidence_hash": proof["raw_message_residual_evidence"]["evidence_hash"],
			"raw_message_connector_evidence_hash": proof["raw_message_connector_evidence"]["evidence_hash"],
			"raw_message_reference_evidence_hash": proof["raw_message_reference_evidence"]["evidence_hash"],
			"raw_message_unsafe_ambiguity_evidence_hash": proof["raw_message_unsafe_ambiguity_evidence"]["evidence_hash"],
		}

	def raw_message_safety_evidence(self, subject_hash, field_name, evidence_type, evidence_status, **overrides):
		evidence = {
			"evidence_id": hash_text(f"{field_name}:{subject_hash}"),
			"evidence_type": evidence_type,
			"evidence_status": evidence_status,
			"evidence_basis": RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE,
			"source_analyzer_id": self.TRUSTED_ANALYZER_ID,
			"source_analyzer_version": self.TRUSTED_ANALYZER_VERSION,
			"derived_from_proposer_roles": False,
			"derived_from_verifier_roles": False,
			"derived_from_semantic_safe_output": False,
			"derived_from_lexical_phrase_authority": False,
			"redaction_status": TRACE_REDACTION_SAFE,
			"blocking_reason": "",
		}
		evidence.update(overrides)
		evidence["evidence_hash"] = raw_message_safety_evidence_hash(evidence)
		return evidence

	def raw_message_safety_proof(self, message, **overrides):
		raw_hash = hash_text(message)
		normalized_hash = hash_text(normalize_message(message))
		subject_hash = raw_message_safety_proof_subject_hash(raw_hash, normalized_hash)
		clause_coverage_evidence = self.raw_message_safety_evidence(
			subject_hash,
			"raw_message_clause_coverage_evidence",
			"clause_coverage",
			"complete",
		)
		secondary_intent_evidence = self.raw_message_safety_evidence(
			subject_hash,
			"raw_message_secondary_intent_evidence",
			"secondary_intent",
			"none",
		)
		mixed_intent_evidence = self.raw_message_safety_evidence(
			subject_hash,
			"raw_message_mixed_intent_evidence",
			"mixed_intent",
			"none",
		)
		residual_evidence = self.raw_message_safety_evidence(
			subject_hash,
			"raw_message_residual_evidence",
			"residual",
			"clear",
		)
		connector_evidence = self.raw_message_safety_evidence(
			subject_hash,
			"raw_message_connector_evidence",
			"connector",
			"accounted",
		)
		reference_evidence = self.raw_message_safety_evidence(
			subject_hash,
			"raw_message_reference_evidence",
			"reference",
			"resolved_or_not_required",
		)
		unsafe_ambiguity_evidence = self.raw_message_safety_evidence(
			subject_hash,
			"raw_message_unsafe_ambiguity_evidence",
			"unsafe_ambiguity",
			"none",
		)
		proof = {
			"registry_status": "approved",
			"raw_message_hash": raw_hash,
			"normalized_message_hash": normalized_hash,
			"safety_proof_subject_hash": subject_hash,
			"validator_safety_analyzer_id": self.TRUSTED_ANALYZER_ID,
			"validator_safety_analyzer_version": self.TRUSTED_ANALYZER_VERSION,
			"raw_message_safety_status": "safe",
			"raw_message_clause_coverage_status": "complete",
			"raw_message_secondary_intent_status": "none",
			"raw_message_mixed_intent_status": "none",
			"raw_message_residual_status": "clear",
			"raw_message_reference_status": "resolved_or_not_required",
			"raw_message_safety_evidence_hash": hash_text(f"safety:{subject_hash}"),
			"raw_message_clause_boundary_evidence_hash": hash_text(f"boundary:{subject_hash}"),
			"raw_message_secondary_intent_evidence_hash": hash_text(f"secondary:{subject_hash}"),
			"raw_message_residual_evidence_hash": hash_text(f"residual:{subject_hash}"),
			"raw_message_reference_evidence_hash": hash_text(f"reference:{subject_hash}"),
			"raw_message_clause_coverage_evidence": clause_coverage_evidence,
			"raw_message_secondary_intent_evidence": secondary_intent_evidence,
			"raw_message_mixed_intent_evidence": mixed_intent_evidence,
			"raw_message_residual_evidence": residual_evidence,
			"raw_message_connector_evidence": connector_evidence,
			"raw_message_reference_evidence": reference_evidence,
			"raw_message_unsafe_ambiguity_evidence": unsafe_ambiguity_evidence,
			"safe_route_authority": ANSWER_MODE_GOVERNED_ERP,
			"safety_proof_basis": RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE,
			"trace_redaction_status": TRACE_REDACTION_SAFE,
		}
		proof["raw_message_safety_evidence_hash"] = unsafe_ambiguity_evidence["evidence_hash"]
		proof["raw_message_clause_boundary_evidence_hash"] = clause_coverage_evidence["evidence_hash"]
		proof["raw_message_secondary_intent_evidence_hash"] = secondary_intent_evidence["evidence_hash"]
		proof["raw_message_residual_evidence_hash"] = residual_evidence["evidence_hash"]
		proof["raw_message_reference_evidence_hash"] = reference_evidence["evidence_hash"]
		deferred = {
			key: overrides.pop(key)
			for key in list(overrides)
			if key in {"safety_proof_id", "safety_proof_payload_hash", "safety_proof_attestation"}
		}
		proof.update(overrides)
		proof["safety_proof_payload_hash"] = raw_message_safety_proof_payload_hash(proof)
		proof["safety_proof_id"] = proof["safety_proof_payload_hash"]
		proof["safety_proof_attestation"] = raw_message_safety_proof_attestation_hash(
			self.TRUSTED_ANALYZER_SECRET,
			proof["safety_proof_payload_hash"],
		)
		proof.update(deferred)
		return proof

	def install_raw_message_safety_proof(self, *proofs):
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY.clear()
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY.update(self.raw_message_safety_analyzer_registry())
		ibc.VALIDATOR_OWNED_SAFETY_PROOF_REGISTRY.clear()
		for index, proof in enumerate(proofs):
			key = proof.get("safety_proof_id") or proof.get("safety_proof_payload_hash") or f"malformed-proof-{index}"
			ibc.VALIDATOR_OWNED_SAFETY_PROOF_REGISTRY[key] = proof

	def install_raw_message_analysis(self, *analyses):
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_REGISTRY.clear()
		for index, analysis in enumerate(analyses):
			key = analysis.get("raw_message_analysis_subject_hash") or f"malformed-analysis-{index}"
			ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_REGISTRY[f"{key}:{index}"] = analysis

	def install_raw_message_analysis_execution(self, *executions):
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_REGISTRY.clear()
		for index, execution in enumerate(executions):
			key = execution.get("run_id") or f"malformed-execution-{index}"
			ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_REGISTRY[key] = execution

	def clear_raw_message_safety_proofs(self):
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY.clear()
		ibc.VALIDATOR_OWNED_SAFETY_PROOF_REGISTRY.clear()
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_REGISTRY.clear()
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_REGISTRY.clear()

	def span(self, message, fragment):
		normalized = normalize_message(message)
		fragment_normalized = normalize_message(fragment)
		start = normalized.find(fragment_normalized)
		self.assertNotEqual(start, -1, fragment)
		return start, start + len(fragment_normalized), fragment_normalized

	def target(self, target_id="item_a", target_type=TARGET_TYPE_ITEM, value="EC7H-ITEM-A"):
		return {
			"target_id": target_id,
			"target_type": target_type,
			"value": value,
			"schema_status": "valid",
		}

	def target_for_erp_value(self, value):
		if value.startswith("EC7H-SUP-"):
			return self.target("supplier_a", TARGET_TYPE_SUPPLIER, value)
		if value.startswith("EC7H-CUST-"):
			return self.target("customer_a", TARGET_TYPE_CUSTOMER, value)
		if value.startswith("EC7H-SINV-"):
			return self.target("invoice_a", TARGET_TYPE_INVOICE, value)
		return self.target("item_a", TARGET_TYPE_ITEM, value)

	def clause(
		self,
		message,
		fragment,
		*,
		clause_id="c1",
		index=0,
		clause_type=CLAUSE_TYPE_FACTUAL_LOOKUP,
		factual=True,
		decision=False,
		advice=False,
		business_action=False,
		policy=False,
		domain=DOMAIN_NONE,
		erp_target_ids=None,
	):
		start, end, text = self.span(message, fragment)
		return {
			"clause_id": clause_id,
			"index": index,
			"start": start,
			"end": end,
			"text": text,
			"clause_type": clause_type,
			"erp_target_ids": erp_target_ids if erp_target_ids is not None else ["item_a"],
			"visible_context_reference_ids": [],
			"factual_lookup_intent": factual,
			"safe_followup_intent": False,
			"decision_intent": decision,
			"advice_intent": advice,
			"business_action_intent": business_action,
			"policy_boundary_intent": policy,
			"business_action_domain": domain,
			"policy_domain": domain if policy else DOMAIN_NONE,
			"ambiguity_status": "none",
		}

	def segmented_safe_clauses(self, message):
		return [
			self.clause(message, "Show item sales", clause_id="c1", index=0),
			self.clause(message, "for EC7H-ITEM-A", clause_id="c2", index=1),
		]

	def mixed_factual_forgery_clauses(self, message):
		return [
			self.clause(message, "Show item sales for EC7H-ITEM-A", clause_id="c1", index=0),
			self.clause(message, "and tell me whether to discount it", clause_id="c2", index=1),
		]

	def proposal(
		self,
		message,
		clauses=None,
		*,
		model_name="light-intent-test",
		proposer_run_id="proposal-run-1",
		include_completeness=True,
		include_embedded_verifier=False,
		lexical_alarm=False,
		targets=None,
	):
		clauses = clauses if clauses is not None else self.segmented_safe_clauses(message)
		payload = {
			"intent_proposer_role": PROPOSER_ROLE_LIGHTWEIGHT,
			"intent_proposer_status": PROPOSER_STATUS_COMPLETE,
			"intent_proposer_confidence": 0.94,
			"intent_proposer_model_name": model_name,
			"intent_proposer_run_id": proposer_run_id,
			"intent_proposer_output_status": PROPOSER_OUTPUT_VALID,
			"proposal_authority_source": PROPOSAL_SOURCE_LIGHTWEIGHT_MODEL,
			"clause_count": len(clauses),
			"clauses": clauses,
			"erp_targets": targets if targets is not None else [self.target()],
			"visible_context_references": [],
			"mixed_intent_detected": any(clause.get("business_action_intent") for clause in clauses)
			and any(clause.get("factual_lookup_intent") for clause in clauses),
			"trace_redaction_status": TRACE_REDACTION_SAFE,
			"lexical_conservative_alarm": lexical_alarm,
			"lexical_alarm_reason": "possible_unmodeled_intent" if lexical_alarm else "",
		}
		if include_completeness:
			payload.update(
				{
					"proposal_completeness_status": COMPLETENESS_STATUS_COMPLETE,
					"clause_segmentation_status": AUDIT_STATUS_PASSED,
					"secondary_intent_audit_status": AUDIT_STATUS_PASSED,
					"residual_audit_status": AUDIT_STATUS_PASSED,
					"clause_role_confidence_status": AUDIT_STATUS_PASSED,
					"full_span_factual_authority": FULL_SPAN_FACTUAL_AUTHORITY_NOT_ALLOWED,
					"full_span_factual_allow_reason": "",
					"natural_language_interpretation_required": True,
					"independent_parse_guard_status": AUDIT_STATUS_PASSED,
				}
			)
		if include_embedded_verifier:
			payload.update(
				{
					"clause_role_verifier_status": AUDIT_STATUS_PASSED,
					"all_clause_roles_verified": True,
					"proposer_verifier_agreement_status": AUDIT_STATUS_PASSED,
					"role_disagreement_policy": ROLE_DISAGREEMENT_POLICY_FAIL_CLOSED,
				}
			)
		return payload

	def verified_clause(self, message, clause, **overrides):
		normalized = normalize_message(message)
		normalized_clause = normalized[clause["start"] : clause["end"]]
		payload = {
			"clause_id": clause["clause_id"],
			"span_start": clause["start"],
			"span_end": clause["end"],
			"normalized_clause_hash": hash_text(normalized_clause),
			"verified_clause_type": clause["clause_type"],
			"verified_factual_lookup_intent": clause["factual_lookup_intent"],
			"verified_safe_followup_intent": clause["safe_followup_intent"],
			"verified_decision_intent": clause["decision_intent"],
			"verified_advice_intent": clause["advice_intent"],
			"verified_business_action_intent": clause["business_action_intent"],
			"verified_policy_boundary_intent": clause["policy_boundary_intent"],
			"verified_business_action_domain": clause["business_action_domain"],
			"verified_policy_domain": clause["policy_domain"],
			"verification_status": "verified",
			"verification_confidence": 0.94,
			"verification_blocking_reason": "",
		}
		payload.update(overrides)
		return payload

	def verifier_envelope(self, message, clauses, **overrides):
		payload = {
			"envelope_version": "v1-ib-a-i.1",
			"raw_message_hash": hash_text(message),
			"normalized_message_hash": hash_text(normalize_message(message)),
			"verifier_source": self.TRUSTED_VERIFIER_SOURCE,
			"verifier_run_id": "verifier-run-1",
			"verifier_model_name": self.TRUSTED_VERIFIER_MODEL,
			"verifier_prompt_version": self.TRUSTED_VERIFIER_PROMPT_VERSION,
			"verifier_status": AUDIT_STATUS_PASSED,
			"verifier_independence_status": "independent",
			"verifier_authority_effect": VERIFIER_AUTHORITY_EFFECT_CONSISTENCY_ONLY,
			"trace_redaction_status": TRACE_REDACTION_SAFE,
			"verified_clauses": [self.verified_clause(message, clause) for clause in clauses],
		}
		deferred = {
			key: overrides.pop(key)
			for key in list(overrides)
			if key in {"verifier_payload_hash", "verifier_attestation"}
		}
		payload.update(overrides)
		return self.sign_envelope(payload, **deferred)

	def sign_envelope(self, envelope, **overrides):
		envelope["verifier_payload_hash"] = canonical_verifier_payload_hash(envelope)
		envelope["verifier_attestation"] = verifier_attestation_hash(
			self.TRUSTED_VERIFIER_SECRET,
			envelope["verifier_payload_hash"],
		)
		envelope.update(overrides)
		return envelope

	def sign_raw_message_safety_proof(self, proof, **overrides):
		proof.update(overrides)
		proof["safety_proof_payload_hash"] = raw_message_safety_proof_payload_hash(proof)
		proof["safety_proof_id"] = proof["safety_proof_payload_hash"]
		proof["safety_proof_attestation"] = raw_message_safety_proof_attestation_hash(
			self.TRUSTED_ANALYZER_SECRET,
			proof["safety_proof_payload_hash"],
		)
		return proof

	def update_raw_message_safety_evidence(self, proof, evidence_field, **updates):
		evidence = dict(proof[evidence_field])
		evidence.update(updates)
		evidence["evidence_hash"] = raw_message_safety_evidence_hash(evidence)
		proof[evidence_field] = evidence
		hash_field_by_evidence = {
			"raw_message_unsafe_ambiguity_evidence": "raw_message_safety_evidence_hash",
			"raw_message_clause_coverage_evidence": "raw_message_clause_boundary_evidence_hash",
			"raw_message_secondary_intent_evidence": "raw_message_secondary_intent_evidence_hash",
			"raw_message_residual_evidence": "raw_message_residual_evidence_hash",
			"raw_message_reference_evidence": "raw_message_reference_evidence_hash",
		}
		hash_field = hash_field_by_evidence.get(evidence_field)
		if hash_field:
			proof[hash_field] = evidence["evidence_hash"]
		return self.sign_raw_message_safety_proof(proof)

	def validate(self, message, proposal, **kwargs):
		return validate_intent_boundary_contract(
			message,
			proposal,
			trusted_verifier_registry=self.trusted_verifier_registry(),
			**kwargs,
		)

	def validate_with_safety_proof(self, message, proposal, clauses, **kwargs):
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof)
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		self.install_raw_message_analysis_execution(self.raw_message_analysis_execution(message, analysis))
		return self.validate(
			message,
			proposal,
			**kwargs,
		)

	def install_safe_asserting_provenance(self, message):
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof)
		execution = self.raw_message_analysis_execution(message, analysis)
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		self.install_raw_message_analysis_execution(execution)
		return proof, analysis, execution

	def strict_safe_subset_proof(self, message):
		return {
			"status": "proven",
			"normalized_message_hash": hash_text(normalize_message(message)),
			"factual_lookup_intent": True,
			"decision_intent": False,
			"advice_intent": False,
			"business_action_intent": False,
			"policy_boundary_intent": False,
			"legal_or_regulatory_advice_intent": False,
			"prediction_score_or_future_cause_intent": False,
			"manipulation_report_hiding_intent": False,
			"write_mutation_workflow_intent": False,
			"unsupported_business_recommendation_intent": False,
			"mixed_intent_detected": False,
			"visible_context_ambiguity": False,
			"unresolved_pronoun_or_reference": False,
			"unsafe_domain_evidence": False,
			"clause_coverage_status": "complete",
			"target_schema_status": "valid",
			"trace_redaction_status": TRACE_REDACTION_SAFE,
			"safe_subset_authority_source": PROPOSAL_SOURCE_DETERMINISTIC_SAFE_SUBSET,
			"mechanical_command_id": "MECH_SHOW_ITEM_SALES",
			"mechanical_command_registry_status": "approved",
			"natural_language_interpretation_required": False,
			"intent_interpretation_required": False,
			"erp_targets": [self.target()],
			"clause_count": 1,
		}

	def assert_no_route(self, contract, expected_error=None):
		payload = contract.to_payload()
		self.assertFalse(payload["report_routing_allowed"])
		self.assertFalse(payload["context_reuse_allowed"])
		self.assertFalse(payload["model_reasoning_allowed"])
		if expected_error:
			self.assertFalse(payload["final_emission_allowed"])
			self.assertEqual(payload["authority_decision"], AUTHORITY_DECISION_BLOCK)
			self.assertIn(expected_error, payload["deterministic_validator_errors"])

	def assert_closure_no_governed_route(self, contract):
		payload = contract.to_payload()
		self.assertFalse(payload["report_routing_allowed"])
		self.assertFalse(payload["context_reuse_allowed"])
		self.assertFalse(payload["model_reasoning_allowed"])
		self.assertFalse(payload["final_emission_allowed"])
		self.assertNotEqual(payload["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
		self.assertNotEqual(payload["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)

	def test_forged_proposer_embedded_verifier_without_external_envelope_fails(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		contract = validate_intent_boundary_contract(
			message,
			self.proposal(message, self.mixed_factual_forgery_clauses(message), include_embedded_verifier=True),
		)
		self.assert_no_route(contract, "external_verifier_envelope_missing")

	def test_mixed_unsafe_forged_all_factual_fails_without_external_envelope(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		contract = validate_intent_boundary_contract(message, self.proposal(message, self.mixed_factual_forgery_clauses(message)))
		self.assert_no_route(contract, "external_verifier_envelope_missing")

	def test_embedded_passed_verifier_still_fails_without_external_envelope(self):
		message = "Show EC7H-ITEM-A item sales and is action needed?"
		clauses = [
			self.clause(message, "Show EC7H-ITEM-A item sales", clause_id="c1", index=0),
			self.clause(message, "and is action needed?", clause_id="c2", index=1),
		]
		contract = validate_intent_boundary_contract(
			message,
			self.proposal(message, clauses, include_embedded_verifier=True),
		)
		self.assert_no_route(contract, "external_verifier_envelope_missing")

	def test_legal_action_prompt_forged_factual_without_envelope_fails(self):
		message = "Show EC7H-ITEM-A item sales and tell me if legal action is allowed"
		clauses = [
			self.clause(message, "Show EC7H-ITEM-A item sales", clause_id="c1", index=0),
			self.clause(message, "and tell me if legal action is allowed", clause_id="c2", index=1),
		]
		contract = validate_intent_boundary_contract(message, self.proposal(message, clauses))
		self.assert_no_route(contract, "external_verifier_envelope_missing")

	def test_missing_verifier_envelope_fails_safe_prompt(self):
		message = "Show item sales for EC7H-ITEM-A"
		contract = validate_intent_boundary_contract(message, self.proposal(message))
		self.assert_no_route(contract, "external_verifier_envelope_missing")

	def test_verifier_envelope_hash_mismatch_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses, normalized_message_hash="bad")
		contract = validate_intent_boundary_contract(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "verifier_envelope_normalized_hash_mismatch")

	def test_forged_external_envelope_from_unknown_source_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses, verifier_source="unknown_verifier")
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "verifier_source_not_trusted")

	def test_forged_envelope_with_fake_nonempty_hash_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses, verifier_payload_hash="fake-non-empty-hash")
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "verifier_payload_hash_mismatch")

	def test_forged_envelope_with_wrong_canonical_hash_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses)
		envelope["verified_clauses"][0]["verification_confidence"] = 0.93
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "verifier_payload_hash_mismatch")

	def test_forged_envelope_missing_attestation_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses)
		del envelope["verifier_attestation"]
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "external_verifier_envelope_missing_fields")
		self.assertIn("verifier_attestation_missing", contract.to_payload()["deterministic_validator_errors"])

	def test_forged_envelope_wrong_attestation_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses, verifier_attestation="wrong-attestation")
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "verifier_attestation_invalid")

	def test_verifier_source_not_in_registry_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses)
		contract = validate_intent_boundary_contract(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "verifier_source_not_trusted")

	def test_verifier_prompt_version_not_approved_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses, verifier_prompt_version="unapproved-prompt")
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "verifier_prompt_version_not_approved")

	def test_verifier_model_name_not_allowed_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses, verifier_model_name="unapproved-model")
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "verifier_model_name_not_allowed")

	def test_verifier_same_source_as_proposer_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses, verifier_source=PROPOSAL_SOURCE_LIGHTWEIGHT_MODEL)
		contract = validate_intent_boundary_contract(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "clause_role_verifier_source_not_independent")

	def test_verifier_same_run_id_as_proposer_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses, verifier_run_id="proposal-run-1")
		contract = validate_intent_boundary_contract(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "clause_role_verifier_run_id_not_independent")

	def test_verifier_partial_clause_map_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses)
		envelope["verified_clauses"] = envelope["verified_clauses"][:1]
		contract = validate_intent_boundary_contract(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "verifier_clause_map_incomplete")

	def test_verifier_proposer_role_disagreement_fails(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		envelope = self.verifier_envelope(message, clauses)
		envelope["verified_clauses"][1].update(
			{
				"verified_clause_type": CLAUSE_TYPE_BUSINESS_ACTION,
				"verified_factual_lookup_intent": False,
				"verified_decision_intent": True,
				"verified_advice_intent": True,
				"verified_business_action_intent": True,
				"verified_policy_boundary_intent": True,
				"verified_business_action_domain": DOMAIN_PRICING_VALUATION_ACTION,
				"verified_policy_domain": DOMAIN_PRICING_VALUATION_ACTION,
			}
		)
		envelope = self.sign_envelope(envelope)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "proposer_verifier_role_disagreement")

	def test_mixed_unsafe_prompt_with_fake_trusted_looking_envelope_fails(self):
		cases = (
			(
				"Show item sales for EC7H-ITEM-A and tell me whether to discount it",
				"Show item sales for EC7H-ITEM-A",
				"and tell me whether to discount it",
			),
			(
				"Show EC7H-ITEM-A item sales and is action needed?",
				"Show EC7H-ITEM-A item sales",
				"and is action needed?",
			),
			(
				"Show EC7H-ITEM-A item sales and tell me if legal action is allowed",
				"Show EC7H-ITEM-A item sales",
				"and tell me if legal action is allowed",
			),
		)
		for message, factual_fragment, forged_fragment in cases:
			with self.subTest(message=message):
				clauses = [
					self.clause(message, factual_fragment, clause_id="c1", index=0),
					self.clause(message, forged_fragment, clause_id="c2", index=1),
				]
				envelope = self.verifier_envelope(message, clauses)
				contract = validate_intent_boundary_contract(message, self.proposal(message, clauses), verifier_envelope=envelope)
				self.assert_no_route(contract, "verifier_source_not_trusted")

	def test_trusted_attested_verifier_agreement_alone_cannot_authorize_report_routing(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assert_no_route(contract, "validator_owned_safety_proof_missing")
		self.assertEqual(payload["clause_role_verifier_provenance_status"], VERIFIER_PROVENANCE_TRUSTED)
		self.assertEqual(payload["role_verification_authority_effect"], "consistency_evidence_only")
		self.assertEqual(payload["validator_owned_safe_route_authority_status"], VALIDATOR_SAFE_ROUTE_BLOCKED_WITHOUT_PROOF)

	def test_required_mixed_prompts_fail_even_with_trusted_verifier_agreement(self):
		cases = (
			(
				"Show item sales for EC7H-ITEM-A and tell me whether to discount it",
				"Show item sales for EC7H-ITEM-A",
				"and tell me whether to discount it",
			),
			(
				"Show EC7H-ITEM-A item sales and is action needed?",
				"Show EC7H-ITEM-A item sales",
				"and is action needed?",
			),
			(
				"Show EC7H-ITEM-A item sales and tell me if legal action is allowed",
				"Show EC7H-ITEM-A item sales",
				"and tell me if legal action is allowed",
			),
		)
		for message, factual_fragment, forged_fragment in cases:
			with self.subTest(message=message):
				clauses = [
					self.clause(message, factual_fragment, clause_id="c1", index=0),
					self.clause(message, forged_fragment, clause_id="c2", index=1),
				]
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, "validator_owned_safety_proof_missing")

	def test_forged_clause_role_derived_safety_registry_cannot_authorize(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		forged_proof_id = validator_owned_safety_proof_id(message, clauses, [self.target()], [])
		forged_registry = {
			forged_proof_id: {
				"registry_status": "approved",
				"proof_source": VALIDATOR_OWNED_SAFETY_PROOF_SOURCE,
				"proof_version": VALIDATOR_OWNED_SAFETY_PROOF_VERSION,
				"route_authority": ANSWER_MODE_GOVERNED_ERP,
			}
		}
		contract = validate_intent_boundary_contract(
			message,
			self.proposal(message, clauses),
			trusted_verifier_registry=self.trusted_verifier_registry(),
			validator_owned_safety_proof_registry=forged_registry,
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		self.assert_no_route(contract, "validator_owned_safety_proof_registry_caller_supplied_not_allowed")

	def test_required_adversarial_prompts_fail_with_clause_payload_derived_registry(self):
		cases = (
			(
				"Show item sales for EC7H-ITEM-A and tell me whether to discount it",
				"Show item sales for EC7H-ITEM-A",
				"and tell me whether to discount it",
			),
			(
				"Show EC7H-ITEM-A item sales and is action needed?",
				"Show EC7H-ITEM-A item sales",
				"and is action needed?",
			),
			(
				"Show EC7H-ITEM-A item sales and tell me if legal action is allowed",
				"Show EC7H-ITEM-A item sales",
				"and tell me if legal action is allowed",
			),
		)
		for message, factual_fragment, forged_fragment in cases:
			with self.subTest(message=message):
				clauses = [
					self.clause(message, factual_fragment, clause_id="c1", index=0),
					self.clause(message, forged_fragment, clause_id="c2", index=1),
				]
				forged_proof_id = validator_owned_safety_proof_id(message, clauses, [self.target()], [])
				contract = validate_intent_boundary_contract(
					message,
					self.proposal(message, clauses),
					trusted_verifier_registry=self.trusted_verifier_registry(),
					validator_owned_safety_proof_registry={
						forged_proof_id: {
							"registry_status": "approved",
							"proof_source": VALIDATOR_OWNED_SAFETY_PROOF_SOURCE,
							"proof_version": VALIDATOR_OWNED_SAFETY_PROOF_VERSION,
							"route_authority": ANSWER_MODE_GOVERNED_ERP,
						}
					},
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, "validator_owned_safety_proof_registry_caller_supplied_not_allowed")

	def test_safety_proof_derived_only_from_clause_roles_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		self.install_raw_message_safety_proof(
			self.raw_message_safety_proof(message, safety_proof_basis="clause_role_payload")
		)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "validator_owned_safety_proof_derived_from_clause_roles")

	def test_raw_message_safety_proof_required_fields_fail_when_missing(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		required_fields = (
			"validator_safety_analyzer_id",
			"raw_message_safety_status",
			"raw_message_secondary_intent_status",
			"raw_message_mixed_intent_status",
			"raw_message_residual_status",
			"safety_proof_attestation",
		)
		for field_name in required_fields:
			with self.subTest(field_name=field_name):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				del proof[field_name]
				self.install_raw_message_safety_proof(proof)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, "validator_owned_safety_proof_missing_raw_message_fields")

	def test_safety_proof_with_route_authority_but_no_raw_message_evidence_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		self.install_raw_message_safety_proof(
			{
				"registry_status": "approved",
				"raw_message_hash": hash_text(message),
				"normalized_message_hash": hash_text(normalize_message(message)),
				"safe_route_authority": ANSWER_MODE_GOVERNED_ERP,
			}
		)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "validator_owned_safety_proof_missing_raw_message_fields")

	def test_no_matching_raw_message_safety_proof_fails_closed(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		payload = contract.to_payload()
		self.assert_no_route(contract, "validator_owned_safety_proof_missing")
		self.assertEqual(payload["validator_owned_safety_proof_uniqueness_status"], "no_matching_proof")
		self.assertEqual(payload["validator_owned_safety_proof_conflict_status"], "none")

	def test_exactly_one_valid_raw_message_safety_proof_may_pass(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		contract = self.validate_with_safety_proof(
			message,
			self.proposal(message, clauses),
			clauses,
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assertTrue(payload["report_routing_allowed"])
		self.assertEqual(payload["validator_owned_safety_proof_uniqueness_status"], "unique")
		self.assertEqual(payload["validator_owned_safety_proof_conflict_status"], "none")
		self.assertEqual(payload["validator_owned_safety_proof_evidence_status"], "present")

	def test_two_matching_safe_proofs_for_same_message_fail_closed(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		first = self.raw_message_safety_proof(message)
		second = self.raw_message_safety_proof(
			message,
			raw_message_safety_evidence_hash=hash_text("alternate-safe-evidence"),
		)
		self.install_raw_message_safety_proof(first, second)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		payload = contract.to_payload()
		self.assert_no_route(contract, "validator_owned_safety_proof_conflict_detected")
		self.assertEqual(payload["validator_owned_safety_proof_uniqueness_status"], "duplicate_subject")
		self.assertEqual(payload["validator_owned_safety_proof_conflict_status"], "conflict_detected")

	def test_safe_and_unsafe_conflicting_proofs_fail_closed(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		safe_proof = self.raw_message_safety_proof(message)
		unsafe_proof = self.raw_message_safety_proof(
			message,
			raw_message_safety_status="unsafe",
			raw_message_secondary_intent_status="present",
			safe_route_authority=ANSWER_MODE_CLARIFICATION,
			raw_message_safety_evidence_hash=hash_text("unsafe-evidence"),
		)
		self.install_raw_message_safety_proof(safe_proof, unsafe_proof)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "validator_owned_safety_proof_conflict_detected")

	def test_proof_registry_insertion_order_cannot_change_route_outcome(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		safe_proof = self.raw_message_safety_proof(message)
		unsafe_proof = self.raw_message_safety_proof(
			message,
			raw_message_safety_status="unsafe",
			raw_message_secondary_intent_status="present",
			safe_route_authority=ANSWER_MODE_CLARIFICATION,
			raw_message_safety_evidence_hash=hash_text("unsafe-evidence"),
		)
		outcomes = []
		for proofs in ((unsafe_proof, safe_proof), (safe_proof, unsafe_proof)):
			self.install_raw_message_safety_proof(*proofs)
			contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
			payload = contract.to_payload()
			outcomes.append(
				(
					payload["report_routing_allowed"],
					payload["model_reasoning_allowed"],
					payload["final_emission_allowed"],
					payload["validator_owned_safety_proof_conflict_status"],
				)
			)
			self.assert_no_route(contract, "validator_owned_safety_proof_conflict_detected")
		self.assertEqual(outcomes[0], outcomes[1])

	def test_registry_key_must_equal_safety_proof_id(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY.clear()
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY.update(self.raw_message_safety_analyzer_registry())
		ibc.VALIDATOR_OWNED_SAFETY_PROOF_REGISTRY.clear()
		ibc.VALIDATOR_OWNED_SAFETY_PROOF_REGISTRY["wrong-registry-key"] = proof
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "validator_owned_safety_proof_registry_key_mismatch")

	def test_missing_safety_proof_id_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		del proof["safety_proof_id"]
		self.install_raw_message_safety_proof(proof)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		payload = contract.to_payload()
		self.assert_no_route(contract, "validator_owned_safety_proof_missing_raw_message_fields")
		self.assertIn("validator_owned_safety_proof_id_missing", payload["deterministic_validator_errors"])

	def test_missing_safety_proof_subject_hash_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		del proof["safety_proof_subject_hash"]
		self.install_raw_message_safety_proof(proof)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		payload = contract.to_payload()
		self.assert_no_route(contract, "validator_owned_safety_proof_missing_raw_message_fields")
		self.assertIn("validator_owned_safety_proof_subject_hash_mismatch", payload["deterministic_validator_errors"])

	def test_missing_raw_message_evidence_hash_fields_fail(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		evidence_fields = (
			"raw_message_safety_evidence_hash",
			"raw_message_clause_boundary_evidence_hash",
			"raw_message_secondary_intent_evidence_hash",
			"raw_message_residual_evidence_hash",
			"raw_message_reference_evidence_hash",
		)
		for field_name in evidence_fields:
			with self.subTest(field_name=field_name):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				del proof[field_name]
				self.install_raw_message_safety_proof(proof)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				payload = contract.to_payload()
				self.assert_no_route(contract, "validator_owned_safety_proof_missing_raw_message_fields")
				self.assertEqual(payload["validator_owned_safety_proof_evidence_status"], "missing")

	def test_empty_raw_message_evidence_hash_fields_fail(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		evidence_fields = (
			"raw_message_safety_evidence_hash",
			"raw_message_clause_boundary_evidence_hash",
			"raw_message_secondary_intent_evidence_hash",
			"raw_message_residual_evidence_hash",
			"raw_message_reference_evidence_hash",
		)
		for field_name in evidence_fields:
			with self.subTest(field_name=field_name):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message, **{field_name: ""})
				self.install_raw_message_safety_proof(proof)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				payload = contract.to_payload()
				self.assert_no_route(contract, "validator_owned_safety_proof_evidence_missing")
				self.assertEqual(payload["validator_owned_safety_proof_evidence_status"], "missing")

	def test_evidence_hash_mutation_after_attestation_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		proof["raw_message_residual_evidence_hash"] = hash_text("mutated-after-attestation")
		self.install_raw_message_safety_proof(proof)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "validator_owned_safety_proof_payload_hash_mismatch")

	def test_status_only_safe_proof_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		raw_hash = hash_text(message)
		normalized_hash = hash_text(normalize_message(message))
		status_only = {
			"registry_status": "approved",
			"raw_message_hash": raw_hash,
			"normalized_message_hash": normalized_hash,
			"safety_proof_subject_hash": raw_message_safety_proof_subject_hash(raw_hash, normalized_hash),
			"validator_safety_analyzer_id": self.TRUSTED_ANALYZER_ID,
			"validator_safety_analyzer_version": self.TRUSTED_ANALYZER_VERSION,
			"raw_message_safety_status": "safe",
			"raw_message_clause_coverage_status": "complete",
			"raw_message_secondary_intent_status": "none",
			"raw_message_mixed_intent_status": "none",
			"raw_message_residual_status": "clear",
			"raw_message_reference_status": "resolved_or_not_required",
			"safe_route_authority": ANSWER_MODE_GOVERNED_ERP,
			"safety_proof_basis": RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE,
			"trace_redaction_status": TRACE_REDACTION_SAFE,
		}
		self.sign_raw_message_safety_proof(status_only)
		self.install_raw_message_safety_proof(status_only)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "validator_owned_safety_proof_missing_raw_message_fields")

	def test_signed_false_safe_proof_without_evidence_fails(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		raw_hash = hash_text(message)
		normalized_hash = hash_text(normalize_message(message))
		false_safe = {
			"registry_status": "approved",
			"raw_message_hash": raw_hash,
			"normalized_message_hash": normalized_hash,
			"safety_proof_subject_hash": raw_message_safety_proof_subject_hash(raw_hash, normalized_hash),
			"validator_safety_analyzer_id": self.TRUSTED_ANALYZER_ID,
			"validator_safety_analyzer_version": self.TRUSTED_ANALYZER_VERSION,
			"raw_message_safety_status": "safe",
			"raw_message_clause_coverage_status": "complete",
			"raw_message_secondary_intent_status": "none",
			"raw_message_mixed_intent_status": "none",
			"raw_message_residual_status": "clear",
			"raw_message_reference_status": "resolved_or_not_required",
			"safe_route_authority": ANSWER_MODE_GOVERNED_ERP,
			"safety_proof_basis": RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE,
			"trace_redaction_status": TRACE_REDACTION_SAFE,
		}
		self.sign_raw_message_safety_proof(false_safe)
		self.install_raw_message_safety_proof(false_safe)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "validator_owned_safety_proof_missing_raw_message_fields")

	def test_signed_false_safe_proof_with_status_only_evidence_hashes_fails(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		proof = self.raw_message_safety_proof(message)
		for field_name in (
			"raw_message_clause_coverage_evidence",
			"raw_message_secondary_intent_evidence",
			"raw_message_mixed_intent_evidence",
			"raw_message_residual_evidence",
			"raw_message_connector_evidence",
			"raw_message_reference_evidence",
			"raw_message_unsafe_ambiguity_evidence",
		):
			del proof[field_name]
		self.sign_raw_message_safety_proof(proof)
		self.install_raw_message_safety_proof(proof)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "validator_owned_safety_proof_missing_raw_message_fields")

	def test_signed_false_safe_proof_with_unsupported_unknown_or_contradictory_evidence_fails(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		cases = (
			("unsupported", "validator_owned_safety_proof_evidence_unsafe_or_ambiguous"),
			("unknown", "validator_owned_safety_proof_evidence_unsafe_or_ambiguous"),
			("contradictory", "validator_owned_safety_proof_evidence_unsafe_or_ambiguous"),
		)
		for evidence_status, expected_error in cases:
			with self.subTest(evidence_status=evidence_status):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				self.update_raw_message_safety_evidence(
					proof,
					"raw_message_unsafe_ambiguity_evidence",
					evidence_status=evidence_status,
					blocking_reason=f"{evidence_status}_evidence",
				)
				self.install_raw_message_safety_proof(proof)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				payload = contract.to_payload()
				self.assert_no_route(contract, expected_error)
				self.assertNotEqual(payload["validator_owned_safety_proof_evidence_semantics_status"], "passed")

	def test_secondary_and_mixed_intent_evidence_contradictions_fail(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		cases = (
			("raw_message_secondary_intent_evidence", "present"),
			("raw_message_mixed_intent_evidence", "mixed"),
		)
		for evidence_field, evidence_status in cases:
			with self.subTest(evidence_field=evidence_field):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				self.update_raw_message_safety_evidence(proof, evidence_field, evidence_status=evidence_status)
				self.install_raw_message_safety_proof(proof)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, "validator_owned_safety_proof_evidence_status_mismatch")
				self.assertIn(
					"validator_owned_safety_proof_evidence_contradicts_proof_status",
					contract.to_payload()["deterministic_validator_errors"],
				)

	def test_connector_residual_and_reference_evidence_unresolved_fail(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		cases = (
			("raw_message_connector_evidence", "unresolved"),
			("raw_message_residual_evidence", "unresolved"),
			("raw_message_reference_evidence", "unresolved"),
		)
		for evidence_field, evidence_status in cases:
			with self.subTest(evidence_field=evidence_field):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				self.update_raw_message_safety_evidence(proof, evidence_field, evidence_status=evidence_status)
				self.install_raw_message_safety_proof(proof)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, "validator_owned_safety_proof_evidence_status_mismatch")

	def test_label_semantic_and_lexical_derived_evidence_fails(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		cases = (
			("derived_from_proposer_roles", "validator_owned_safety_proof_evidence_derived_from_proposer_roles"),
			("derived_from_verifier_roles", "validator_owned_safety_proof_evidence_derived_from_verifier_roles"),
			("derived_from_semantic_safe_output", "validator_owned_safety_proof_evidence_derived_from_semantic_safe_output"),
			("derived_from_lexical_phrase_authority", "validator_owned_safety_proof_evidence_derived_from_lexical_phrase_authority"),
		)
		for derivation_field, expected_error in cases:
			with self.subTest(derivation_field=derivation_field):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				self.update_raw_message_safety_evidence(proof, "raw_message_unsafe_ambiguity_evidence", **{derivation_field: True})
				self.install_raw_message_safety_proof(proof)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, expected_error)

	def test_evidence_redaction_failure_or_raw_business_text_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		cases = (
			({"redaction_status": "unsafe"}, "validator_owned_safety_proof_evidence_redaction_not_safe"),
			({"blocking_reason": "EC7H-ITEM-A"}, "validator_owned_safety_proof_evidence_raw_business_text"),
		)
		for updates, expected_error in cases:
			with self.subTest(expected_error=expected_error):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				self.update_raw_message_safety_evidence(proof, "raw_message_clause_coverage_evidence", **updates)
				self.install_raw_message_safety_proof(proof)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, expected_error)

	def test_safe_factual_prompt_requires_complete_non_derived_evidence_semantics(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		contract = self.validate_with_safety_proof(
			message,
			self.proposal(message, clauses),
			clauses,
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assertTrue(payload["report_routing_allowed"])
		self.assertEqual(payload["validator_owned_safety_proof_evidence_status"], "present")
		self.assertEqual(payload["validator_owned_safety_proof_evidence_semantics_status"], "passed")

	def test_signed_false_safe_proof_without_raw_message_analysis_fails(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		self.install_raw_message_safety_proof(self.raw_message_safety_proof(message))
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "validator_owned_raw_message_analysis_missing")

	def test_raw_message_analysis_missing_subject_hash_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof)
		del analysis["raw_message_analysis_subject_hash"]
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "validator_owned_raw_message_analysis_missing_fields")

	def test_raw_message_analysis_subject_mismatch_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof, raw_message_analysis_subject_hash="wrong-subject")
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "validator_owned_raw_message_analysis_subject_mismatch")

	def test_raw_message_analysis_unsafe_ambiguous_or_unknown_status_fails(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		for analysis_status in ("unsafe", "ambiguous", "unknown"):
			with self.subTest(analysis_status=analysis_status):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				analysis = self.raw_message_analysis(message, proof, analysis_status=analysis_status)
				self.install_raw_message_safety_proof(proof)
				self.install_raw_message_analysis(analysis)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, "validator_owned_raw_message_analysis_not_safe")

	def test_raw_message_analysis_status_contradictions_fail(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		cases = (
			("raw_message_secondary_intent_status", "present", "validator_owned_raw_message_analysis_secondary_intent_contradicts_proof"),
			("raw_message_mixed_intent_status", "mixed", "validator_owned_raw_message_analysis_mixed_intent_contradicts_proof"),
			("raw_message_connector_status", "unresolved", "validator_owned_raw_message_analysis_connector_contradicts_proof"),
			("raw_message_residual_status", "unresolved", "validator_owned_raw_message_analysis_residual_contradicts_proof"),
			("raw_message_reference_status", "unresolved", "validator_owned_raw_message_analysis_reference_contradicts_proof"),
		)
		for field_name, field_value, expected_error in cases:
			with self.subTest(field_name=field_name):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				analysis = self.raw_message_analysis(message, proof, **{field_name: field_value})
				self.install_raw_message_safety_proof(proof)
				self.install_raw_message_analysis(analysis)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, expected_error)

	def test_raw_message_analysis_derivation_sources_fail(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		cases = (
			"derived_from_proposer_roles",
			"derived_from_verifier_roles",
			"derived_from_semantic_safe_output",
			"derived_from_lexical_phrase_authority",
		)
		for derivation_field in cases:
			with self.subTest(derivation_field=derivation_field):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				analysis = self.raw_message_analysis(message, proof, **{derivation_field: True})
				self.install_raw_message_safety_proof(proof)
				self.install_raw_message_analysis(analysis)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, f"validator_owned_raw_message_analysis_{derivation_field}")

	def test_raw_message_analysis_evidence_hash_mismatch_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(
			message,
			proof,
			raw_message_secondary_intent_evidence_hash=hash_text("mismatched-analysis-evidence"),
		)
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		payload = contract.to_payload()
		self.assert_no_route(contract, "validator_owned_raw_message_analysis_evidence_hash_mismatch")
		self.assertEqual(payload["validator_owned_raw_message_analysis_evidence_match_status"], "mismatch")

	def test_required_unsafe_prompts_fail_even_if_proof_evidence_claims_safe(self):
		cases = (
			(
				"Show item sales for EC7H-ITEM-A and tell me whether to discount it",
				"Show item sales for EC7H-ITEM-A",
				"and tell me whether to discount it",
			),
			(
				"Show EC7H-ITEM-A item sales and is action needed?",
				"Show EC7H-ITEM-A item sales",
				"and is action needed?",
			),
			(
				"Show EC7H-ITEM-A item sales and tell me if legal action is allowed",
				"Show EC7H-ITEM-A item sales",
				"and tell me if legal action is allowed",
			),
		)
		for message, factual_fragment, forged_fragment in cases:
			with self.subTest(message=message):
				self.clear_raw_message_safety_proofs()
				clauses = [
					self.clause(message, factual_fragment, clause_id="c1", index=0),
					self.clause(message, forged_fragment, clause_id="c2", index=1),
				]
				proof = self.raw_message_safety_proof(message)
				analysis = self.raw_message_analysis(message, proof, analysis_status="unsafe")
				self.install_raw_message_safety_proof(proof)
				self.install_raw_message_analysis(analysis)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, "validator_owned_raw_message_analysis_not_safe")

	def test_detect_raw_message_unsafe_evidence_is_conservative_not_permissive(self):
		evidence = detect_raw_message_unsafe_evidence(normalize_message("Show item sales for EC7H-ITEM-A"))
		self.assertTrue(evidence["has_unsafe_evidence"])
		self.assertTrue(evidence["raw_text_conservative_alarm"])
		self.assertFalse(evidence["can_authorize"])
		self.assertEqual(evidence["authority_effect"], LEXICAL_AUTHORITY_EFFECT_RESTRICT_ONLY)

	def test_analysis_registry_entry_without_execution_proof_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof)
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "analysis_execution_missing")

	def test_analysis_execution_missing_run_id_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof)
		execution = self.raw_message_analysis_execution(message, analysis, run_id="")
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		self.install_raw_message_analysis_execution(execution)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "analysis_execution_run_id_missing")

	def test_analysis_execution_missing_or_mismatched_input_hash_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		for updates, expected_error in (
			({"input_hash": ""}, "analysis_execution_input_hash_missing"),
			({"input_hash": hash_text("wrong-input")}, "analysis_execution_input_hash_mismatch"),
		):
			with self.subTest(expected_error=expected_error):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				analysis = self.raw_message_analysis(message, proof)
				execution = self.raw_message_analysis_execution(message, analysis, **updates)
				self.install_raw_message_safety_proof(proof)
				self.install_raw_message_analysis(analysis)
				self.install_raw_message_analysis_execution(execution)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, expected_error)

	def test_analysis_execution_missing_or_mismatched_output_hash_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		for updates, expected_error in (
			({"output_hash": ""}, "analysis_execution_output_hash_missing"),
			({"output_hash": hash_text("wrong-output")}, "analysis_execution_output_hash_mismatch"),
		):
			with self.subTest(expected_error=expected_error):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				analysis = self.raw_message_analysis(message, proof)
				execution = self.raw_message_analysis_execution(message, analysis, **updates)
				self.install_raw_message_safety_proof(proof)
				self.install_raw_message_analysis(analysis)
				self.install_raw_message_analysis_execution(execution)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, expected_error)

	def test_analysis_execution_missing_artifact_hash_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof)
		execution = self.raw_message_analysis_execution(message, analysis, artifact_hash="")
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		self.install_raw_message_analysis_execution(execution)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "analysis_execution_artifact_hash_missing")

	def test_analysis_execution_invalid_attestation_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof)
		execution = self.raw_message_analysis_execution(message, analysis, attestation="wrong-attestation")
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		self.install_raw_message_analysis_execution(execution)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "analysis_execution_attestation_invalid")

	def test_analysis_execution_status_source_and_replay_failures(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		cases = (
			({"execution_status": "started"}, "analysis_execution_status_not_completed"),
			({"execution_source": "caller_supplied_execution"}, "analysis_execution_source_not_validator_owned"),
			({"trace_redaction_status": "unsafe"}, "analysis_execution_trace_redaction_not_safe"),
			({"replay_status": "not_verified"}, "analysis_execution_replay_not_verified"),
		)
		for updates, expected_error in cases:
			with self.subTest(expected_error=expected_error):
				self.clear_raw_message_safety_proofs()
				proof = self.raw_message_safety_proof(message)
				analysis = self.raw_message_analysis(message, proof)
				execution = self.raw_message_analysis_execution(message, analysis, **updates)
				self.install_raw_message_safety_proof(proof)
				self.install_raw_message_analysis(analysis)
				self.install_raw_message_analysis_execution(execution)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, expected_error)

	def test_analysis_execution_analyzer_version_not_approved_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof)
		execution = self.raw_message_analysis_execution(message, analysis, analyzer_version="unapproved-version")
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		self.install_raw_message_analysis_execution(execution)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "analysis_execution_analyzer_version_mismatch")

	def test_signed_proof_safe_analysis_and_forged_execution_proof_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof)
		execution = self.raw_message_analysis_execution(message, analysis)
		execution["artifact_hash"] = hash_text("mutated-artifact-after-attestation")
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		self.install_raw_message_analysis_execution(execution)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "analysis_execution_payload_hash_mismatch")

	def test_required_unsafe_prompts_fail_without_valid_executed_analyzer_proof(self):
		cases = (
			(
				"Show item sales for EC7H-ITEM-A and tell me whether to discount it",
				"Show item sales for EC7H-ITEM-A",
				"and tell me whether to discount it",
			),
			(
				"Show EC7H-ITEM-A item sales and is action needed?",
				"Show EC7H-ITEM-A item sales",
				"and is action needed?",
			),
			(
				"Show EC7H-ITEM-A item sales and tell me if legal action is allowed",
				"Show EC7H-ITEM-A item sales",
				"and tell me if legal action is allowed",
			),
		)
		for message, factual_fragment, forged_fragment in cases:
			with self.subTest(message=message):
				self.clear_raw_message_safety_proofs()
				clauses = [
					self.clause(message, factual_fragment, clause_id="c1", index=0),
					self.clause(message, forged_fragment, clause_id="c2", index=1),
				]
				proof = self.raw_message_safety_proof(message)
				analysis = self.raw_message_analysis(message, proof)
				self.install_raw_message_safety_proof(proof)
				self.install_raw_message_analysis(analysis)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, "analysis_execution_missing")

	def test_false_safe_provenance_over_unsafe_mixed_prompt_fails_replay(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = self.mixed_factual_forgery_clauses(message)
		self.install_safe_asserting_provenance(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assert_no_route(contract, "validator_owned_replayed_raw_message_safety_not_safe")
		self.assertEqual(payload["replayed_raw_message_safety_status"], "replayed")
		self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "blocked")
		self.assertIn("connector_requires_replay_segmentation", payload["replayed_raw_message_safety_blocking_reason"])

	def test_stored_analysis_safe_but_replayed_analyzer_unsafe_fails(self):
		message = "Show EC7H-ITEM-A item sales and is action needed?"
		clauses = [
			self.clause(message, "Show EC7H-ITEM-A item sales", clause_id="c1", index=0),
			self.clause(message, "and is action needed?", clause_id="c2", index=1),
		]
		self.install_safe_asserting_provenance(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assertEqual(payload["validator_owned_raw_message_analysis_status"], "safe")
		self.assert_no_route(contract, "validator_owned_replayed_raw_message_safety_not_safe")
		self.assertEqual(payload["replayed_raw_message_safety_evidence_match_status"], "mismatch")

	def test_replay_status_verified_without_validator_recompute_config_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		self.install_safe_asserting_provenance(message)
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY[self.TRUSTED_ANALYZER_ID].pop(
			"replay_config_hash",
			None,
		)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assertEqual(payload["analysis_execution_replay_status"], "verified")
		self.assert_no_route(contract, "validator_owned_replayed_raw_message_safety_not_safe")
		self.assertIn("validator_owned_replay_config_missing", payload["replayed_raw_message_safety_blocking_reason"])

	def test_signed_execution_without_reproducible_replay_artifact_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		self.install_safe_asserting_provenance(message)
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY[self.TRUSTED_ANALYZER_ID].pop(
			"replay_artifact_hash",
			None,
		)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assert_no_route(contract, "validator_owned_replayed_raw_message_safety_not_safe")
		self.assertIn("validator_owned_replay_artifact_missing", payload["replayed_raw_message_safety_blocking_reason"])

	def test_proposer_verifier_agreement_cannot_override_replayed_unsafe(self):
		message = "Show EC7H-ITEM-A item sales and tell me if legal action is allowed"
		clauses = [
			self.clause(message, "Show EC7H-ITEM-A item sales", clause_id="c1", index=0),
			self.clause(message, "and tell me if legal action is allowed", clause_id="c2", index=1),
		]
		self.install_safe_asserting_provenance(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assertTrue(payload["proposer_verifier_agreement_status"])
		self.assert_no_route(contract, "validator_owned_replayed_raw_message_safety_not_safe")

	def test_mixed_factual_second_intent_classes_fail_replayed_safety(self):
		cases = (
			("Show EC7H-ITEM-A item sales and tell me whether to discount it", "and tell me whether to discount it"),
			("Show EC7H-ITEM-A item sales and is action needed?", "and is action needed?"),
			("Show EC7H-ITEM-A item sales and tell me if legal action is allowed", "and tell me if legal action is allowed"),
			("Show EC7H-ITEM-A item sales and tell me whether to delay payment", "and tell me whether to delay payment"),
			("Show EC7H-ITEM-A item sales and tell me whether to hide it from the report", "and tell me whether to hide it from the report"),
			("Show EC7H-ITEM-A item sales and tell me whether it will sell next month", "and tell me whether it will sell next month"),
		)
		for message, unsafe_fragment in cases:
			with self.subTest(message=message):
				self.clear_raw_message_safety_proofs()
				clauses = [
					self.clause(message, "Show EC7H-ITEM-A item sales", clause_id="c1", index=0),
					self.clause(message, unsafe_fragment, clause_id="c2", index=1),
				]
				self.install_safe_asserting_provenance(message)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, "validator_owned_replayed_raw_message_safety_not_safe")

	def test_missing_residual_connector_or_reference_evidence_fails_replay_path(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = [self.clause(message, "Show item sales for EC7H-ITEM-A")]
		self.install_safe_asserting_provenance(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assert_no_route(contract, "unresolved_residual_text")
		self.assertFalse(payload["report_routing_allowed"])
		self.assertFalse(payload["model_reasoning_allowed"])
		self.assertFalse(payload["final_emission_allowed"])

		self.clear_raw_message_safety_proofs()
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proposal = self.proposal(message, clauses)
		proposal["visible_context_references"] = [
			{
				"reference_id": "r1",
				"reference_type": "pronoun",
				"resolution_status": "unresolved",
				"read_only_intent": True,
			}
		]
		proposal["clauses"][0]["visible_context_reference_ids"] = ["r1"]
		self.install_safe_asserting_provenance(message)
		contract = self.validate(message, proposal, verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "unresolved_visible_context_reference")

	def test_duplicate_or_conflicting_execution_replay_artifacts_fail(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof)
		execution_a = self.raw_message_analysis_execution(message, analysis, run_id="analysis-run-a")
		execution_b = self.raw_message_analysis_execution(
			message,
			analysis,
			run_id="analysis-run-b",
			artifact_hash=hash_text("different-replay-artifact"),
		)
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		self.install_raw_message_analysis_execution(execution_a, execution_b)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		self.assert_no_route(contract, "analysis_execution_conflict_detected")

	def test_stale_replay_for_different_raw_or_normalized_hash_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		stale_message = "Show EC7H-ITEM-A item price"
		clauses = self.segmented_safe_clauses(message)
		proof = self.raw_message_safety_proof(message)
		analysis = self.raw_message_analysis(message, proof)
		stale_proof = self.raw_message_safety_proof(stale_message)
		stale_analysis = self.raw_message_analysis(stale_message, stale_proof)
		stale_execution = self.raw_message_analysis_execution(stale_message, stale_analysis)
		self.install_raw_message_safety_proof(proof)
		self.install_raw_message_analysis(analysis)
		self.install_raw_message_analysis_execution(stale_execution)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		self.assert_no_route(contract, "analysis_execution_missing")

	def test_single_clause_unsafe_erp_id_prompts_require_positive_safe_replay_shape(self):
		cases = (
			"Tell me whether to discount EC7H-ITEM-A",
			"Should EC7H-ITEM-A be repriced",
			"Recommend discounting EC7H-ITEM-A",
			"Decide if EC7H-ITEM-A should stay in catalog",
			"Explain whether EC7H-ITEM-A is overpriced",
			"Give legal advice for EC7H-ITEM-A",
			"Hide EC7H-ITEM-A from report",
			"Please tell me whether to discount EC7H-ITEM-A",
			"Could you recommend discounting EC7H-ITEM-A",
		)
		for message in cases:
			with self.subTest(message=message):
				self.clear_raw_message_safety_proofs()
				clauses = [self.clause(message, message)]
				self.install_safe_asserting_provenance(message)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				payload = contract.to_payload()
				self.assert_no_route(contract, "validator_owned_replayed_raw_message_safety_not_safe")
				self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "blocked")
				self.assertIn(
					"validator_owned_replay_positive_safe_factual_lookup_not_proven",
					payload["replayed_raw_message_safety_blocking_reason"],
				)

	def test_positive_safe_factual_replay_controls_pass_with_full_invariants(self):
		cases = (
			("Show EC7H-ITEM-A item sales", "EC7H-ITEM-A"),
			("Show EC7H-ITEM-A item price", "EC7H-ITEM-A"),
			("Show EC7H-SUP-A payable status", "EC7H-SUP-A"),
			("Show EC7H-CUST-A outstanding balance", "EC7H-CUST-A"),
			("Show EC7H-SINV-0001 invoice details", "EC7H-SINV-0001"),
		)
		for message, target_value in cases:
			with self.subTest(message=message):
				self.clear_raw_message_safety_proofs()
				target = self.target_for_erp_value(target_value)
				clauses = [self.clause(message, message, erp_target_ids=[target["target_id"]])]
				self.install_safe_asserting_provenance(message)
				contract = self.validate(
					message,
					self.proposal(message, clauses, targets=[target]),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				payload = contract.to_payload()
				self.assertTrue(payload["report_routing_allowed"])
				self.assertTrue(payload["model_reasoning_allowed"])
				self.assertTrue(payload["final_emission_allowed"])
				self.assertEqual(payload["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
				self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "safe")
				self.assertEqual(payload["replayed_raw_message_safety_evidence_match_status"], "matched")

	def test_positive_safe_factual_replay_controls_pass_with_question_punctuation(self):
		cases = (
			("What is the item price for EC7H-ITEM-A?", "EC7H-ITEM-A"),
			("Show EC7H-ITEM-A item sales?", "EC7H-ITEM-A"),
			("Show EC7H-SUP-A payable status?", "EC7H-SUP-A"),
			("Show EC7H-CUST-A outstanding balance?", "EC7H-CUST-A"),
			("Show EC7H-SINV-0001 invoice details?", "EC7H-SINV-0001"),
		)
		for message, target_value in cases:
			with self.subTest(message=message):
				self.clear_raw_message_safety_proofs()
				target = self.target_for_erp_value(target_value)
				clauses = [self.clause(message, message, erp_target_ids=[target["target_id"]])]
				self.install_safe_asserting_provenance(message)
				contract = self.validate(
					message,
					self.proposal(message, clauses, targets=[target]),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				payload = contract.to_payload()
				self.assertTrue(payload["report_routing_allowed"])
				self.assertTrue(payload["model_reasoning_allowed"])
				self.assertTrue(payload["final_emission_allowed"])
				self.assertEqual(payload["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
				self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "safe")
				self.assertEqual(payload["replayed_raw_message_safety_evidence_match_status"], "matched")
				self.assertNotIn("interrogative_requires_non_factual_replay", payload["replayed_raw_message_safety_blocking_reason"])

	def test_unsafe_question_punctuation_remains_blocked_without_positive_safe_replay(self):
		cases = (
			"Should EC7H-ITEM-A be repriced?",
			"Tell me whether to discount EC7H-ITEM-A?",
			"Recommend discounting EC7H-ITEM-A?",
			"Give legal advice for EC7H-ITEM-A?",
			"Hide EC7H-ITEM-A from report?",
		)
		for message in cases:
			with self.subTest(message=message):
				self.clear_raw_message_safety_proofs()
				clauses = [self.clause(message, message)]
				self.install_safe_asserting_provenance(message)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				payload = contract.to_payload()
				self.assert_no_route(contract, "validator_owned_replayed_raw_message_safety_not_safe")
				self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "blocked")

	def test_unsafe_no_question_punctuation_remains_blocked_without_positive_safe_replay(self):
		cases = (
			"Tell me whether to discount EC7H-ITEM-A",
			"Should EC7H-ITEM-A be repriced",
			"Give legal advice for EC7H-ITEM-A",
			"Hide EC7H-ITEM-A from report",
		)
		for message in cases:
			with self.subTest(message=message):
				self.clear_raw_message_safety_proofs()
				clauses = [self.clause(message, message)]
				self.install_safe_asserting_provenance(message)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				payload = contract.to_payload()
				self.assert_no_route(contract, "validator_owned_replayed_raw_message_safety_not_safe")
				self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "blocked")

	def test_sibling_adversarial_replay_prompts_fail_closed(self):
		cases = (
			"Show EC7H-ITEM-A item price recommendation?",
			"Show EC7H-ITEM-A item price with discount advice?",
			"Show EC7H-ITEM-A item sales; recommend discount",
			"Show EC7H-ITEM-A item sales then decide discount",
			"Show EC7H-ITEM-A item sales and decide if price should change",
			"Show EC7H-ITEM-A item sales, should we discount it",
		)
		for message in cases:
			with self.subTest(message=message):
				self.clear_raw_message_safety_proofs()
				clauses = [self.clause(message, message)]
				self.install_safe_asserting_provenance(message)
				contract = self.validate(
					message,
					self.proposal(message, clauses),
					semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				payload = contract.to_payload()
				self.assertFalse(payload["report_routing_allowed"])
				self.assertFalse(payload["context_reuse_allowed"])
				self.assertFalse(payload["model_reasoning_allowed"])
				self.assertFalse(payload["final_emission_allowed"])
				self.assertNotEqual(payload["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
				self.assertNotEqual(payload["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)
				self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "blocked")

	def test_safe_factual_no_question_control_passes_positive_replay(self):
		message = "What is the item price for EC7H-ITEM-A"
		clauses = [self.clause(message, message)]
		self.install_safe_asserting_provenance(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assertTrue(payload["report_routing_allowed"])
		self.assertTrue(payload["model_reasoning_allowed"])
		self.assertTrue(payload["final_emission_allowed"])
		self.assertEqual(payload["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
		self.assertEqual(payload["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)
		self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "safe")

	def test_v1_ib_a_q_closure_authority_model_requires_positive_validator_owned_replay(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)

		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		self.assert_closure_no_governed_route(contract)
		self.assertIn("validator_owned_safety_proof_missing", contract.to_payload()["deterministic_validator_errors"])

		self.clear_raw_message_safety_proofs()
		self.install_safe_asserting_provenance(message)
		ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY[self.TRUSTED_ANALYZER_ID].pop(
			"replay_config_hash",
			None,
		)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assert_closure_no_governed_route(contract)
		self.assertEqual(payload["analysis_execution_replay_status"], "verified")
		self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "blocked")

		self.clear_raw_message_safety_proofs()
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		self.assert_closure_no_governed_route(contract)

		self.clear_raw_message_safety_proofs()
		contract = self.validate(
			message,
			self.proposal(message, clauses, model_name="regex_classifier"),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		self.assert_closure_no_governed_route(contract)
		self.assertIn("lexical_classifier_cannot_authorize", contract.to_payload()["deterministic_validator_errors"])

		self.clear_raw_message_safety_proofs()
		ambiguous_message = "Tell me about EC7H-ITEM-A"
		ambiguous_clauses = [self.clause(ambiguous_message, ambiguous_message)]
		self.install_safe_asserting_provenance(ambiguous_message)
		contract = self.validate(
			ambiguous_message,
			self.proposal(ambiguous_message, ambiguous_clauses),
			semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
			verifier_envelope=self.verifier_envelope(ambiguous_message, ambiguous_clauses),
		)
		payload = contract.to_payload()
		self.assert_closure_no_governed_route(contract)
		self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "blocked")

		self.clear_raw_message_safety_proofs()
		self.install_safe_asserting_provenance(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assertTrue(payload["report_routing_allowed"])
		self.assertTrue(payload["model_reasoning_allowed"])
		self.assertTrue(payload["final_emission_allowed"])
		self.assertEqual(payload["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
		self.assertEqual(payload["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)
		self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "safe")

	def test_ambiguous_or_unproven_replay_result_keeps_all_route_flags_false(self):
		message = "Tell me about EC7H-ITEM-A"
		clauses = [self.clause(message, message)]
		self.install_safe_asserting_provenance(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assert_no_route(contract, "validator_owned_replayed_raw_message_safety_not_safe")
		self.assertFalse(payload["report_routing_allowed"])
		self.assertFalse(payload["context_reuse_allowed"])
		self.assertFalse(payload["model_reasoning_allowed"])
		self.assertFalse(payload["final_emission_allowed"])

	def test_unsafe_mixed_prompt_blocks_with_valid_trusted_verifier_identifying_unsafe_intent(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = [
			self.clause(message, "Show item sales for EC7H-ITEM-A", clause_id="c1", index=0),
			self.clause(
				message,
				"and tell me whether to discount it",
				clause_id="c2",
				index=1,
				clause_type=CLAUSE_TYPE_BUSINESS_ACTION,
				factual=False,
				decision=True,
				advice=True,
				business_action=True,
				policy=True,
				domain=DOMAIN_PRICING_VALUATION_ACTION,
			),
		]
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assertFalse(payload["report_routing_allowed"])
		self.assertFalse(payload["context_reuse_allowed"])
		self.assertFalse(payload["model_reasoning_allowed"])
		self.assertFalse(payload["final_emission_allowed"])
		self.assertNotEqual(payload["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)

	def test_verifier_low_confidence_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		envelope = self.verifier_envelope(message, clauses)
		envelope["verified_clauses"][0]["verification_confidence"] = 0.2
		envelope = self.sign_envelope(envelope)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "clause_role_verification_confidence_too_low")

	def test_verifier_safe_but_residual_unresolved_fails(self):
		message = "Show item sales for EC7H-ITEM-A and tell me whether to discount it"
		clauses = [self.clause(message, "Show item sales for EC7H-ITEM-A")]
		envelope = self.verifier_envelope(message, clauses)
		contract = self.validate(message, self.proposal(message, clauses), verifier_envelope=envelope)
		self.assert_no_route(contract, "unresolved_residual_text")

	def test_verifier_safe_but_pronoun_reference_unresolved_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		proposal = self.proposal(message, clauses)
		proposal["visible_context_references"] = [
			{
				"reference_id": "r1",
				"reference_type": "pronoun",
				"resolution_status": "unresolved",
				"read_only_intent": True,
			}
		]
		proposal["clauses"][0]["visible_context_reference_ids"] = ["r1"]
		contract = self.validate(message, proposal, verifier_envelope=self.verifier_envelope(message, clauses))
		self.assert_no_route(contract, "unresolved_visible_context_reference")

	def test_semantic_unsafe_blocks_even_with_valid_verifier(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		contract = self.validate_with_safety_proof(
			message,
			self.proposal(message, clauses),
			clauses,
			semantic_backstop={"status": SEMANTIC_BACKSTOP_UNSAFE},
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assert_no_route(contract, "validator_owned_safety_proof_semantic_restricted")
		self.assertFalse(payload["final_emission_allowed"])
		self.assertEqual(payload["required_answer_mode"], ANSWER_MODE_CLARIFICATION)

	def test_semantic_safe_cannot_override_missing_envelope(self):
		message = "Show item sales for EC7H-ITEM-A"
		contract = validate_intent_boundary_contract(
			message,
			self.proposal(message),
			semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
		)
		self.assert_no_route(contract, "external_verifier_envelope_missing")

	def test_semantic_safe_cannot_replace_validator_owned_safety_proof(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		self.assert_no_route(contract, "validator_owned_safety_proof_missing")

	def test_safe_single_clause_factual_with_trusted_verifier_fails_without_safety_proof(self):
		message = "Show EC7H-ITEM-A item sales"
		clauses = [self.clause(message, message)]
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		self.assert_no_route(contract, "validator_owned_safety_proof_missing")

	def test_safe_multi_clause_factual_with_trusted_verifier_fails_without_safety_proof(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		self.assert_no_route(contract, "validator_owned_safety_proof_missing")

	def test_safe_single_clause_factual_may_pass_with_validator_owned_safety_proof(self):
		message = "Show EC7H-ITEM-A item sales"
		clauses = [self.clause(message, message)]
		contract = self.validate_with_safety_proof(
			message,
			self.proposal(message, clauses),
			clauses,
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assertTrue(payload["report_routing_allowed"])
		self.assertTrue(payload["model_reasoning_allowed"])
		self.assertTrue(payload["final_emission_allowed"])
		self.assertEqual(payload["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
		self.assertEqual(payload["validator_owned_safe_route_authority_status"], VALIDATOR_SAFE_ROUTE_PROVEN)
		self.assertEqual(payload["replayed_raw_message_safety_status"], "replayed")
		self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "safe")
		self.assertEqual(payload["replayed_raw_message_safety_evidence_match_status"], "matched")

	def test_safe_multi_clause_factual_may_pass_with_validator_owned_safety_proof(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		contract = self.validate_with_safety_proof(
			message,
			self.proposal(message, clauses),
			clauses,
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assertTrue(payload["report_routing_allowed"])
		self.assertEqual(payload["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)
		self.assertEqual(payload["natural_language_report_authority_status"], NATURAL_LANGUAGE_REPORT_AUTHORITY_VERIFIED)
		self.assertEqual(payload["validator_owned_safety_proof_status"], "passed")
		self.assertEqual(payload["replayed_raw_message_safety_status"], "replayed")
		self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "safe")
		self.assertEqual(payload["replayed_raw_message_safety_evidence_match_status"], "matched")

	def test_mechanical_registry_path_still_fails_while_registry_empty(self):
		message = "Show item sales for EC7H-ITEM-A"
		contract = validate_intent_boundary_contract(
			message,
			None,
			strict_deterministic_safe_subset=self.strict_safe_subset_proof(message),
		)
		self.assert_no_route(contract, "strict_safe_subset_command_not_validator_owned")
		self.assertEqual(strict_deterministic_safe_subset_definition()["validator_owned_mechanical_registry_count"], 0)

	def test_model_reasoning_and_final_emission_block_when_verifier_authority_fails(self):
		message = "Show item sales for EC7H-ITEM-A"
		contract = validate_intent_boundary_contract(message, self.proposal(message))
		payload = contract.to_payload()
		self.assertFalse(payload["model_reasoning_allowed"])
		self.assertFalse(payload["final_emission_allowed"])

	def test_lexical_and_pattern_sources_still_block(self):
		message = "Show item sales for EC7H-ITEM-A"
		for model_name in ("regex_classifier", "keyword_classifier", "pattern_classifier"):
			with self.subTest(model_name=model_name):
				clauses = self.segmented_safe_clauses(message)
				contract = self.validate(
					message,
					self.proposal(message, clauses, model_name=model_name),
					verifier_envelope=self.verifier_envelope(message, clauses),
				)
				self.assert_no_route(contract, "lexical_classifier_cannot_authorize")

	def test_lexical_alarm_still_restricts(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses, lexical_alarm=True),
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		payload = contract.to_payload()
		self.assert_no_route(contract, "lexical_conservative_alarm_restricts_routing")
		self.assertEqual(payload["lexical_authority_effect"], LEXICAL_AUTHORITY_EFFECT_RESTRICT_ONLY)

	def test_semantic_ambiguous_restricts_with_valid_verifier(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		contract = self.validate(
			message,
			self.proposal(message, clauses),
			semantic_backstop={"status": SEMANTIC_BACKSTOP_AMBIGUOUS},
			verifier_envelope=self.verifier_envelope(message, clauses),
		)
		self.assert_no_route(contract)
		self.assertEqual(contract.to_payload()["required_answer_mode"], ANSWER_MODE_CLARIFICATION)

	def test_trace_verifier_metadata_redaction_safe(self):
		message = "Show item sales for EC7H-ITEM-A"
		clauses = self.segmented_safe_clauses(message)
		payload = self.validate_with_safety_proof(
			message,
			self.proposal(message, clauses),
			clauses,
			verifier_envelope=self.verifier_envelope(message, clauses),
		).to_payload()
		self.assertEqual(payload["clause_role_verifier_source"], self.TRUSTED_VERIFIER_SOURCE)
		self.assertEqual(payload["clause_role_verifier_authority_effect"], VERIFIER_AUTHORITY_EFFECT_CONSISTENCY_ONLY)
		self.assertEqual(payload["clause_role_verifier_provenance_status"], VERIFIER_PROVENANCE_TRUSTED)
		self.assertEqual(payload["clause_role_verifier_payload_hash_status"], VERIFIER_PAYLOAD_HASH_MATCHED)
		self.assertEqual(payload["clause_role_verifier_attestation_status"], VERIFIER_ATTESTATION_VERIFIED)
		self.assertEqual(payload["role_verification_authority_effect"], "consistency_evidence_only")
		self.assertEqual(payload["semantic_backstop_authority_effect"], "restrict_only")
		self.assertEqual(payload["lexical_evidence_authority_effect"], "restrict_only")
		self.assertEqual(payload["validator_owned_safety_proof_status"], "passed")
		self.assertEqual(payload["validator_owned_safe_route_authority_status"], VALIDATOR_SAFE_ROUTE_PROVEN)
		self.assertEqual(payload["validator_owned_safety_proof_source"], VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_SOURCE)
		self.assertEqual(payload["validator_owned_safety_proof_version"], VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_PROOF_VERSION)
		self.assertEqual(payload["validator_owned_raw_message_safety_status"], "safe")
		self.assertEqual(payload["validator_owned_raw_message_secondary_intent_status"], "none")
		self.assertEqual(payload["validator_owned_safety_proof_basis"], RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE)
		self.assertEqual(payload["validator_owned_safety_proof_evidence_status"], "present")
		self.assertEqual(payload["validator_owned_safety_proof_evidence_semantics_status"], "passed")
		self.assertEqual(payload["validator_owned_raw_message_analysis_status"], "safe")
		self.assertEqual(
			payload["validator_owned_raw_message_analysis_source"],
			ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_SOURCE,
		)
		self.assertEqual(payload["validator_owned_raw_message_analysis_evidence_match_status"], "matched")
		self.assertEqual(payload["analysis_execution_source"], ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_SOURCE)
		self.assertEqual(payload["analysis_execution_status"], "completed")
		self.assertTrue(payload["analysis_execution_run_id"])
		self.assertEqual(payload["analysis_execution_replay_status"], "verified")
		self.assertEqual(payload["replayed_raw_message_safety_source"], ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_SOURCE)
		self.assertEqual(payload["replayed_raw_message_safety_status"], "replayed")
		self.assertEqual(payload["replayed_raw_message_safety_final_decision"], "safe")
		self.assertEqual(payload["replayed_raw_message_safety_evidence_match_status"], "matched")
		self.assertTrue(payload["all_clause_roles_verified"])
		self.assertIn("verified_clause_type", payload["clauses"][0])
		self.assertNotIn("text", payload["clauses"][0])
		self.assertNotIn("value", payload["erp_targets"][0])
		self.assertNotIn("EC7H-ITEM-A", str(payload))
		self.assertNotIn("item sales", str(payload))


if __name__ == "__main__":
	unittest.main()
