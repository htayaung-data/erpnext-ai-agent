import unittest

from ai_assistant_ui.qwen_chat.runtime_metadata_contract import (
	ALLOWED_LANE_CLASSES,
	ALLOWED_METADATA_STATUSES,
	ALLOWED_MODEL_ROLES,
	ALLOWED_STRICT_READINESS_STATUSES,
	LANE_CLASS_AI_REASONING,
	LANE_CLASS_AI_SEMANTIC,
	LANE_CLASS_CONTROL_META,
	LANE_CLASS_DETERMINISTIC_REPORT,
	LANE_CLASS_ERROR_FALLBACK,
	LANE_CLASS_GOVERNED_TOOL_RUNTIME,
	LANE_CLASS_MODEL_BACKED_HELPER,
	LANE_CLASS_POLICY_BOUNDARY,
	LANE_CLASS_SHADOW_OBSERVER,
	METADATA_STATUS_COVERED,
	METADATA_STATUS_MISSING,
	METADATA_STATUS_NEEDS_RUNTIME_PROBE,
	METADATA_STATUS_NOT_APPLICABLE,
	ROLE_CONTROL_META,
	ROLE_DETERMINISTIC,
	ROLE_HEAVY_REASONING,
	ROLE_LIGHT_SEMANTIC,
	ROLE_MODEL_BACKED_HELPER,
	ROLE_GOVERNED_TOOL_RUNTIME,
	ROLE_NOT_APPLICABLE,
	ROLE_POLICY_BOUNDARY,
	ROLE_SHADOW_OBSERVER,
	ROLE_UNKNOWN,
	STRICT_STATUS_NOT_APPLICABLE,
	STRICT_STATUS_NOT_READY_MISSING_METADATA,
	STRICT_STATUS_NOT_READY_RUNTIME_PROBE_REQUIRED,
	STRICT_STATUS_READY,
	STRICT_STATUS_SOFT_BLOCK,
	allowed_runtime_metadata_values,
	build_runtime_metadata_envelope,
	validate_runtime_metadata_envelope,
)


class RuntimeMetadataContractTests(unittest.TestCase):
	def test_allowed_values_include_required_roles_classes_and_statuses(self):
		values = allowed_runtime_metadata_values()

		self.assertEqual(set(values["model_roles"]), ALLOWED_MODEL_ROLES)
		self.assertEqual(set(values["lane_classes"]), ALLOWED_LANE_CLASSES)
		self.assertEqual(set(values["metadata_statuses"]), ALLOWED_METADATA_STATUSES)
		self.assertEqual(set(values["strict_readiness_statuses"]), ALLOWED_STRICT_READINESS_STATUSES)

	def test_ai_semantic_requires_model_name_and_fallback_metadata_before_strict_ready(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="fresh_query_interpretation",
			lane_class=LANE_CLASS_AI_SEMANTIC,
			model_role=ROLE_LIGHT_SEMANTIC,
			model_name="",
			role_compliance="compliant",
			metadata_source="runtime_agent_meta",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_MISSING)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_NOT_READY_MISSING_METADATA)
		self.assertIn("model_name", envelope["missing_fields"])
		self.assertIn("fallback_used", envelope["missing_fields"])
		self.assertFalse(envelope["strict_enforcement_ready"])

	def test_ai_reasoning_with_complete_metadata_is_strict_ready_but_not_enforced(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="business_reasoning_answer",
			lane_class=LANE_CLASS_AI_REASONING,
			model_role=ROLE_HEAVY_REASONING,
			model_name="qwen-heavy-reasoning",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="reasoning_contract",
			evidence_scope="grounded_turn_context",
			answer_mode="erp_business_reasoning",
			preflight_status="passed",
			metadata_source="runtime_agent_meta",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_COVERED)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertTrue(envelope["strict_enforcement_ready"])
		self.assertEqual(validate_runtime_metadata_envelope(envelope)["valid"], True)

	def test_ai_lane_with_fallback_soft_blocks_even_with_metadata(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="frontdoor_semantic_classification",
			lane_class=LANE_CLASS_AI_SEMANTIC,
			model_role=ROLE_LIGHT_SEMANTIC,
			model_name="qwen-light-semantic",
			fallback_used=True,
			fallback_reason="runtime_timeout",
			role_compliance="compliant",
			metadata_source="runtime_agent_meta",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_COVERED)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_SOFT_BLOCK)
		self.assertFalse(envelope["strict_enforcement_ready"])

	def test_model_backed_helper_with_complete_metadata_is_strict_ready_for_provenance_only(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="frontdoor_render",
			lane_class=LANE_CLASS_MODEL_BACKED_HELPER,
			model_role=ROLE_MODEL_BACKED_HELPER,
			model_name="qwen-helper-render",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="frontdoor_contract",
			evidence_scope="frontdoor_response_payload",
			answer_mode="frontdoor_render",
			preflight_status="passed",
			metadata_source="frontdoor_render_runtime_agent_meta",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_COVERED)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertEqual(envelope["expected_model_role"], ROLE_MODEL_BACKED_HELPER)
		self.assertEqual(envelope["compatible_model_roles"], [ROLE_MODEL_BACKED_HELPER])
		self.assertTrue(validate_runtime_metadata_envelope(envelope)["valid"])

	def test_governed_tool_runtime_with_complete_metadata_is_strict_ready_for_tool_provenance_only(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="fresh_query_compiled_read_runtime",
			lane_class=LANE_CLASS_GOVERNED_TOOL_RUNTIME,
			model_role=ROLE_GOVERNED_TOOL_RUNTIME,
			model_name="qwen-tool-runtime",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="compiled_query_contract",
			evidence_scope="governed_report_tool_trace",
			answer_mode="compiled_read_query",
			preflight_status="passed",
			metadata_source="compiled_read_runtime_agent_meta",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_COVERED)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertEqual(envelope["expected_model_role"], ROLE_GOVERNED_TOOL_RUNTIME)
		self.assertEqual(envelope["compatible_model_roles"], [ROLE_GOVERNED_TOOL_RUNTIME])
		self.assertTrue(validate_runtime_metadata_envelope(envelope)["valid"])

	def test_model_backed_helper_with_fallback_soft_blocks_strict_readiness(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="artifact_narrative",
			lane_class=LANE_CLASS_MODEL_BACKED_HELPER,
			model_role=ROLE_MODEL_BACKED_HELPER,
			model_name="qwen-helper-render",
			fallback_used=True,
			fallback_reason="runtime_error",
			role_compliance="compliant",
			authority_source="artifact_context",
			evidence_scope="governed_artifact",
			answer_mode="artifact_narrative",
			preflight_status="passed",
			metadata_source="artifact_narrative_runtime_agent_meta",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_COVERED)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_SOFT_BLOCK)
		self.assertFalse(envelope["strict_enforcement_ready"])
		self.assertTrue(validate_runtime_metadata_envelope(envelope)["valid"])

	def test_governed_tool_runtime_missing_metadata_cannot_be_strict_ready(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="composite_read_step_runtime",
			lane_class=LANE_CLASS_GOVERNED_TOOL_RUNTIME,
			model_role=ROLE_GOVERNED_TOOL_RUNTIME,
			model_name="unknown",
			fallback_used=None,
			role_compliance="unknown",
			authority_source="compiled_query_contract",
			answer_mode="compiled_read_query",
			preflight_status="passed",
			metadata_source="compiled_read_runtime_agent_meta",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_MISSING)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_NOT_READY_MISSING_METADATA)
		self.assertIn("model_name", envelope["missing_fields"])
		self.assertIn("fallback_used", envelope["missing_fields"])
		self.assertIn("role_compliance", envelope["missing_fields"])
		self.assertFalse(envelope["strict_enforcement_ready"])

	def test_provenance_helper_roles_reject_business_answer_roles(self):
		self.assert_role_lane_mismatch(
			lane_class=LANE_CLASS_MODEL_BACKED_HELPER,
			model_role=ROLE_HEAVY_REASONING,
		)
		self.assert_role_lane_mismatch(
			lane_class=LANE_CLASS_GOVERNED_TOOL_RUNTIME,
			model_role=ROLE_DETERMINISTIC,
		)

	def test_provenance_helper_authority_source_does_not_change_role_or_lane_class(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="artifact_narrative",
			lane_class=LANE_CLASS_MODEL_BACKED_HELPER,
			model_role=ROLE_MODEL_BACKED_HELPER,
			model_name="qwen-helper-render",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="governed_erp_report",
			evidence_scope="governed_artifact",
			answer_mode="artifact_narrative",
			preflight_status="passed",
			metadata_source="artifact_narrative_runtime_agent_meta",
		)

		self.assertEqual(envelope["lane_class"], LANE_CLASS_MODEL_BACKED_HELPER)
		self.assertEqual(envelope["model_role"], ROLE_MODEL_BACKED_HELPER)
		self.assertNotEqual(envelope["lane_class"], LANE_CLASS_DETERMINISTIC_REPORT)
		self.assertNotEqual(envelope["model_role"], ROLE_HEAVY_REASONING)
		self.assertNotIn("final_answer_authority", envelope)
		self.assertTrue(validate_runtime_metadata_envelope(envelope)["valid"])

	def test_deterministic_report_declares_authority_and_is_not_applicable_for_strict_ai(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="compiled_support_result_answer",
			lane_class=LANE_CLASS_DETERMINISTIC_REPORT,
			model_role=ROLE_DETERMINISTIC,
			model_name="none",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="governed_erp_report",
			evidence_scope="grounded_turn_context",
			answer_mode="new_query",
			preflight_status="passed",
			metadata_source="deterministic_construction",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_COVERED)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_NOT_APPLICABLE)
		self.assertFalse(envelope["strict_enforcement_ready"])

	def test_policy_boundary_requires_bounded_preflight_and_boundary_role(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="runtime_gate",
			lane_class=LANE_CLASS_POLICY_BOUNDARY,
			model_role=ROLE_POLICY_BOUNDARY,
			model_name="none",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="policy_boundary",
			answer_mode="domain_boundary",
			preflight_status="bounded",
			metadata_source="policy_boundary_contract",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_COVERED)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_NOT_APPLICABLE)
		self.assertNotIn("preflight_status", envelope["missing_fields"])

	def test_policy_boundary_without_bounded_preflight_is_missing_metadata(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="runtime_gate",
			lane_class=LANE_CLASS_POLICY_BOUNDARY,
			model_role=ROLE_POLICY_BOUNDARY,
			model_name="none",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="policy_boundary",
			answer_mode="domain_boundary",
			preflight_status="passed",
			metadata_source="policy_boundary_contract",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_MISSING)
		self.assertIn("preflight_status", envelope["missing_fields"])

	def test_control_meta_can_be_explicit_not_applicable(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="clarification_control",
			lane_class=LANE_CLASS_CONTROL_META,
			model_role=ROLE_NOT_APPLICABLE,
			model_name="none",
			fallback_used=False,
			role_compliance="not_applicable",
			authority_source="control_meta",
			answer_mode="clarification_show_options",
			preflight_status="passed",
			metadata_source="control_meta_authority",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_NOT_APPLICABLE)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_NOT_APPLICABLE)
		self.assertTrue(envelope["role_lane_compatible"])

	def test_control_meta_accepts_control_meta_role(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="service_compound_stop",
			lane_class=LANE_CLASS_CONTROL_META,
			model_role=ROLE_CONTROL_META,
			model_name="none",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="control_meta",
			answer_mode="compound_stop",
			preflight_status="passed",
			metadata_source="control_meta_authority",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_COVERED)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_NOT_APPLICABLE)
		self.assertTrue(validate_runtime_metadata_envelope(envelope)["valid"])

	def test_error_fallback_accepts_not_applicable_role(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="legacy_runtime_client_error",
			lane_class=LANE_CLASS_ERROR_FALLBACK,
			model_role=ROLE_NOT_APPLICABLE,
			model_name="none",
			fallback_used=False,
			role_compliance="not_applicable",
			authority_source="error_fallback",
			answer_mode="runtime_client_error",
			preflight_status="passed",
			metadata_source="error_fallback_authority",
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_NOT_APPLICABLE)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_NOT_APPLICABLE)
		self.assertTrue(validate_runtime_metadata_envelope(envelope)["valid"])

	def test_shadow_observer_requires_runtime_probe_when_requested(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="nbu_shadow_observation",
			lane_class=LANE_CLASS_SHADOW_OBSERVER,
			model_role=ROLE_SHADOW_OBSERVER,
			model_name="qwen-light-semantic",
			fallback_used=False,
			role_compliance="compliant",
			metadata_source="nbu_shadow_runtime_agent_meta",
			runtime_probe_required=True,
		)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_NEEDS_RUNTIME_PROBE)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_NOT_READY_RUNTIME_PROBE_REQUIRED)
		self.assertFalse(envelope["strict_enforcement_ready"])

	def test_unknown_role_is_allowed_only_as_not_ready_inventory_state(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="unknown_lane",
			lane_class="unknown",
			model_role=ROLE_UNKNOWN,
			metadata_source="dry_run_inventory",
		)
		validation = validate_runtime_metadata_envelope(envelope)

		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_MISSING)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_NOT_READY_MISSING_METADATA)
		self.assertFalse(envelope["strict_enforcement_ready"])
		self.assertTrue(validation["valid"])

	def assert_role_lane_mismatch(self, *, lane_class, model_role):
		envelope = build_runtime_metadata_envelope(
			lane_id="mismatch_probe",
			lane_class=lane_class,
			model_role=model_role,
			model_name="qwen-test",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="test_authority",
			preflight_status="bounded" if lane_class == LANE_CLASS_POLICY_BOUNDARY else "passed",
			metadata_source="contract_test",
		)
		validation = validate_runtime_metadata_envelope(envelope)

		self.assertNotEqual(envelope["metadata_status"], METADATA_STATUS_COVERED)
		self.assertNotEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(envelope["role_lane_compatible"])
		self.assertIn("role_lane_mismatch", envelope["missing_fields"])
		self.assertTrue(validation["role_lane_mismatch"])
		self.assertFalse(validation["valid"])

	def test_deterministic_report_rejects_light_semantic_role(self):
		self.assert_role_lane_mismatch(
			lane_class=LANE_CLASS_DETERMINISTIC_REPORT,
			model_role=ROLE_LIGHT_SEMANTIC,
		)

	def test_policy_boundary_rejects_deterministic_role(self):
		self.assert_role_lane_mismatch(
			lane_class=LANE_CLASS_POLICY_BOUNDARY,
			model_role=ROLE_DETERMINISTIC,
		)

	def test_shadow_observer_rejects_light_semantic_role(self):
		self.assert_role_lane_mismatch(
			lane_class=LANE_CLASS_SHADOW_OBSERVER,
			model_role=ROLE_LIGHT_SEMANTIC,
		)

	def test_ai_semantic_rejects_heavy_reasoning_role(self):
		self.assert_role_lane_mismatch(
			lane_class=LANE_CLASS_AI_SEMANTIC,
			model_role=ROLE_HEAVY_REASONING,
		)

	def assert_forged_envelope_invalid(self, envelope, expected_key):
		validation = validate_runtime_metadata_envelope(envelope)

		self.assertFalse(validation["valid"])
		self.assertTrue(validation[expected_key], validation)

	def test_forged_ai_semantic_strict_ready_with_unknown_model_is_invalid(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="frontdoor_semantic_classification",
			lane_class=LANE_CLASS_AI_SEMANTIC,
			model_role=ROLE_LIGHT_SEMANTIC,
			model_name="unknown",
			fallback_used=False,
			role_compliance="compliant",
			metadata_source="runtime_agent_meta",
		)
		envelope.update(
			metadata_status=METADATA_STATUS_COVERED,
			strict_readiness_status=STRICT_STATUS_READY,
			strict_enforcement_ready=True,
			missing_fields=[],
		)

		self.assert_forged_envelope_invalid(envelope, "missing_fields_omitted")
		validation = validate_runtime_metadata_envelope(envelope)
		self.assertIn("model_name", validation["recomputed_missing_fields"])

	def test_forged_ai_semantic_strict_ready_with_missing_fallback_state_is_invalid(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="frontdoor_semantic_classification",
			lane_class=LANE_CLASS_AI_SEMANTIC,
			model_role=ROLE_LIGHT_SEMANTIC,
			model_name="qwen-light-semantic",
			fallback_used=None,
			role_compliance="compliant",
			metadata_source="runtime_agent_meta",
		)
		envelope.update(
			metadata_status=METADATA_STATUS_COVERED,
			strict_readiness_status=STRICT_STATUS_READY,
			strict_enforcement_ready=True,
			missing_fields=[],
		)

		self.assert_forged_envelope_invalid(envelope, "missing_fields_omitted")
		validation = validate_runtime_metadata_envelope(envelope)
		self.assertIn("fallback_used", validation["recomputed_missing_fields"])

	def test_forged_ai_semantic_strict_ready_with_fallback_used_is_invalid(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="frontdoor_semantic_classification",
			lane_class=LANE_CLASS_AI_SEMANTIC,
			model_role=ROLE_LIGHT_SEMANTIC,
			model_name="qwen-light-semantic",
			fallback_used=True,
			role_compliance="compliant",
			metadata_source="runtime_agent_meta",
		)
		envelope.update(
			strict_readiness_status=STRICT_STATUS_READY,
			strict_enforcement_ready=True,
		)

		self.assert_forged_envelope_invalid(envelope, "strict_readiness_status_mismatch")

	def test_forged_deterministic_report_covered_without_authority_source_is_invalid(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="compiled_support_result_answer",
			lane_class=LANE_CLASS_DETERMINISTIC_REPORT,
			model_role=ROLE_DETERMINISTIC,
			model_name="none",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="",
			preflight_status="passed",
			metadata_source="deterministic_construction",
		)
		envelope.update(metadata_status=METADATA_STATUS_COVERED, missing_fields=[])

		self.assert_forged_envelope_invalid(envelope, "missing_fields_omitted")

	def test_forged_policy_boundary_covered_with_passed_preflight_is_invalid(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="runtime_gate",
			lane_class=LANE_CLASS_POLICY_BOUNDARY,
			model_role=ROLE_POLICY_BOUNDARY,
			model_name="none",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="policy_boundary",
			preflight_status="passed",
			metadata_source="policy_boundary_contract",
		)
		envelope.update(metadata_status=METADATA_STATUS_COVERED, missing_fields=[])

		self.assert_forged_envelope_invalid(envelope, "missing_fields_omitted")

	def test_forged_control_meta_covered_without_authority_source_is_invalid(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="clarification_control",
			lane_class=LANE_CLASS_CONTROL_META,
			model_role=ROLE_CONTROL_META,
			model_name="none",
			fallback_used=False,
			role_compliance="compliant",
			authority_source="",
			preflight_status="passed",
			metadata_source="control_meta_authority",
		)
		envelope.update(metadata_status=METADATA_STATUS_COVERED, missing_fields=[])

		self.assert_forged_envelope_invalid(envelope, "missing_fields_omitted")

	def test_strict_enforcement_ready_true_is_invalid_when_recomputed_not_ready(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="nbu_shadow_observation",
			lane_class=LANE_CLASS_SHADOW_OBSERVER,
			model_role=ROLE_SHADOW_OBSERVER,
			model_name="qwen-light-semantic",
			fallback_used=False,
			role_compliance="compliant",
			metadata_source="nbu_shadow_runtime_agent_meta",
			runtime_probe_required=True,
		)
		envelope["strict_enforcement_ready"] = True

		self.assert_forged_envelope_invalid(envelope, "strict_enforcement_ready_mismatch")

	def test_supplied_empty_missing_fields_invalid_when_recomputed_missing_fields_exist(self):
		envelope = build_runtime_metadata_envelope(
			lane_id="fresh_query_interpretation",
			lane_class=LANE_CLASS_AI_SEMANTIC,
			model_role=ROLE_LIGHT_SEMANTIC,
			model_name="unknown",
			role_compliance="compliant",
			metadata_source="runtime_agent_meta",
		)
		envelope["missing_fields"] = []

		self.assert_forged_envelope_invalid(envelope, "missing_fields_omitted")


if __name__ == "__main__":
	unittest.main()
