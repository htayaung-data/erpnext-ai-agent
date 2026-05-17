import unittest

from ai_assistant_ui.qwen_chat.composite_artifact_registry import (
	run_composite_artifact_registry_probe,
	validate_composite_artifact_registry,
	validate_composite_assembly_registry,
	validate_composite_compatibility_registry,
	validate_composite_family_registry,
)
from ai_assistant_ui.qwen_chat.metadata import (
	get_composite_artifact_spec,
	get_composite_assembly_spec,
	get_composite_compatibility_spec,
	get_composite_family_spec,
	get_governed_kpi_execution_spec,
	load_composite_artifact_registry,
	load_composite_assembly_registry,
	load_composite_compatibility_registry,
	load_composite_family_registry,
)


def _activation_states():
	return [
		"active",
		"blocked_missing_policy",
		"blocked_missing_data",
		"draft_unapproved",
		"deprecated",
	]


class TestCompositeArtifactRegistry(unittest.TestCase):
	def test_current_composite_registry_payloads_validate(self):
		family_result = validate_composite_family_registry()
		compatibility_result = validate_composite_compatibility_registry()
		assembly_result = validate_composite_assembly_registry()
		artifact_result = validate_composite_artifact_registry()

		self.assertEqual(family_result.status, "pass", family_result.errors)
		self.assertEqual(compatibility_result.status, "pass", compatibility_result.errors)
		self.assertEqual(assembly_result.status, "pass", assembly_result.errors)
		self.assertEqual(artifact_result.status, "pass", artifact_result.errors)
		self.assertEqual(family_result.stats.get("family_count"), 3)
		self.assertEqual(compatibility_result.stats.get("compatibility_rule_count"), 3)
		self.assertEqual(assembly_result.stats.get("assembly_count"), 3)
		self.assertEqual(artifact_result.stats.get("artifact_count"), 5)

	def test_loader_accessors_are_copy_safe_and_return_current_specs(self):
		family_payload = load_composite_family_registry()
		artifact_payload = load_composite_artifact_registry()
		compatibility_payload = load_composite_compatibility_registry()
		assembly_payload = load_composite_assembly_registry()
		baseline_family_count = len(family_payload.get("families") or [])
		baseline_artifact_count = len(artifact_payload.get("artifacts") or [])
		baseline_compatibility_count = len(compatibility_payload.get("rules") or [])
		baseline_assembly_count = len(assembly_payload.get("assemblies") or [])

		family_payload["families"].append({"family_id": "mutated"})
		artifact_payload["artifacts"].append({"composite_id": "mutated"})
		compatibility_payload["rules"].append({"compatibility_rule_id": "mutated"})
		assembly_payload["assemblies"].append({"assembly_id": "mutated"})

		self.assertEqual(len(load_composite_family_registry().get("families") or []), baseline_family_count)
		self.assertEqual(len(load_composite_artifact_registry().get("artifacts") or []), baseline_artifact_count)
		self.assertEqual(len(load_composite_compatibility_registry().get("rules") or []), baseline_compatibility_count)
		self.assertEqual(len(load_composite_assembly_registry().get("assemblies") or []), baseline_assembly_count)
		self.assertEqual(
			get_composite_family_spec("customer_commercial_ranking").get("activation_state"),
			"active",
		)
		self.assertEqual(
			get_composite_artifact_spec("customer_risk_as_of_default_composite").get("composite_kind"),
			"risk_table",
		)
		self.assertEqual(
			get_composite_compatibility_spec("customer_risk_as_of_same_scope_metrics").get("activation_state"),
			"active",
		)
		self.assertEqual(
			get_composite_assembly_spec("customer_as_of_risk_ranking_assembly").get("row_missing_component_policy"),
			"degrade_row_keep_primary",
		)

	def test_customer_risk_as_of_family_artifact_and_assembly_are_active_after_3_4c(self):
		family = get_composite_family_spec("customer_risk_as_of")
		artifact = get_composite_artifact_spec("customer_risk_as_of_default_composite")
		assembly = get_composite_assembly_spec("customer_as_of_risk_ranking_assembly")

		self.assertEqual(family.get("activation_state"), "active")
		self.assertEqual(family.get("default_primary_metric"), "overdue_amount")
		self.assertIn("collection_recommendation", family.get("blocked_variations") or [])
		self.assertEqual(artifact.get("activation_state"), "active")
		self.assertEqual(artifact.get("blocked_reason"), "")
		self.assertEqual(assembly.get("activation_state"), "active")

	def test_customer_risk_as_of_component_executions_expose_family_metric_ids(self):
		expected = {
			"customer_overdue_amount_as_of_ranking_execution": "overdue_amount",
			"customer_overdue_ratio_as_of_ranking_execution": "overdue_ratio",
			"credit_utilization_customer_as_of_ranking_execution": "credit_utilization",
		}

		for execution_id, family_metric_id in expected.items():
			with self.subTest(execution_id=execution_id):
				spec = get_governed_kpi_execution_spec(execution_id)
				value_mapping = spec.get("value_metric_mapping") if isinstance(spec.get("value_metric_mapping"), dict) else {}
				self.assertEqual(value_mapping.get("family_metric_id"), family_metric_id)

	def test_family_validator_rejects_unsupported_variation_axis(self):
		result = validate_composite_family_registry(
			{
				"contract_version": "1.0",
				"status": "test",
				"description": "test",
				"allowed_activation_states": _activation_states(),
				"allowed_entity_grains": ["customer"],
				"allowed_time_scope_types": ["period_required"],
				"allowed_variation_axes": ["period"],
				"allowed_limit_policies": ["top_n"],
				"allowed_sort_directions": ["desc"],
				"allowed_clarification_policies": ["clarify_scope"],
				"families": [
					{
						"family_id": "bad_family",
						"label": "Bad Family",
						"owner": "finance",
						"company_scope": ["global"],
						"entity_grain": "customer",
						"time_scope_type": "period_required",
						"supported_variation_axes": ["basis"],
						"supported_variation_values": {"basis": ["sales_order"]},
						"allowed_primary_metrics": ["revenue"],
						"allowed_secondary_metrics": ["quantity"],
						"default_sort_direction": "desc",
						"default_limit_policy": "top_n",
						"clarification_policy": "clarify_scope",
						"activation_state": "draft_unapproved",
						"blocked_reason": "test"
					}
				]
			}
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(any("unsupported axis" in message for message in result.errors), result.errors)

	def test_artifact_validator_rejects_unknown_family_reference(self):
		result = validate_composite_artifact_registry(
			{
				"contract_version": "1.0",
				"status": "test",
				"description": "test",
				"allowed_activation_states": _activation_states(),
				"allowed_composite_kinds": ["ranking_table"],
				"allowed_render_styles": ["business_table"],
				"artifacts": [
					{
						"composite_id": "bad_artifact",
						"family_id": "missing_family",
						"label": "Bad Artifact",
						"composite_kind": "ranking_table",
						"entity_grain": "customer",
						"time_scope_type": "period_required",
						"variation_requirements": {"basis": "sales_order"},
						"primary_metric_id": "revenue",
						"secondary_metric_ids": ["quantity"],
						"required_execution_ids": ["missing_execution"],
						"assembly_id": "missing_assembly",
						"compatibility_rule_ids": ["missing_rule"],
						"render_style": "business_table",
						"activation_state": "draft_unapproved",
						"blocked_reason": "test"
					}
				]
			},
			composite_family_payload={"families": []},
			composite_compatibility_payload={"rules": []},
			composite_assembly_payload={"assemblies": []},
		)
		self.assertEqual(result.status, "fail")
		self.assertTrue(any("unknown family" in message for message in result.errors), result.errors)

	def test_registry_probe_reports_ok(self):
		probe = run_composite_artifact_registry_probe()
		self.assertTrue(probe.get("ok"), probe)
