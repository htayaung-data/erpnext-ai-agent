import unittest

from ai_assistant_ui.qwen_chat.live_trace_evidence_protocol import (
	REDACTED_VALUE,
	build_minimal_redacted_live_trace_fixture,
	missing_live_trace_fields,
	redact_live_trace_record,
	required_live_trace_fields,
	trace_storage_policy,
	validate_live_trace_fixture,
)


class LiveTraceEvidenceProtocolTests(unittest.TestCase):
	def test_minimal_redacted_fixture_is_valid_and_has_no_runtime_effect(self):
		fixture = build_minimal_redacted_live_trace_fixture()

		result = validate_live_trace_fixture(fixture)

		self.assertTrue(result["valid"])
		self.assertEqual(result["runtime_effect"], "none")
		self.assertEqual(result["missing_fields"], [])
		self.assertGreaterEqual(len(required_live_trace_fields()), 25)

	def test_missing_required_fields_are_reported(self):
		fixture = build_minimal_redacted_live_trace_fixture()
		del fixture["lane_id"]
		del fixture["authorized_emission"]["emitted"]

		self.assertEqual(
			missing_live_trace_fields(fixture),
			["lane_id", "authorized_emission.emitted"],
		)
		self.assertFalse(validate_live_trace_fixture(fixture)["valid"])

	def test_redaction_removes_sensitive_text_but_preserves_metadata(self):
		record = build_minimal_redacted_live_trace_fixture(
			user_text="Show customer ACME invoice INV-0001 for 12000 USD",
			model_output={"answer_text": "ACME owes 12000 USD"},
			entity_name="ACME Ltd",
		)

		redacted = redact_live_trace_record(record)

		self.assertNotIn("user_text", redacted)
		self.assertNotIn("model_output", redacted)
		self.assertNotIn("entity_name", redacted)
		self.assertEqual(redacted["lane_id"], "frontdoor_semantic_classification")
		self.assertTrue(validate_live_trace_fixture(redacted)["valid"])

	def test_unredacted_sensitive_fields_are_invalid(self):
		fixture = build_minimal_redacted_live_trace_fixture(
			user_text="raw customer question",
			redaction_status="redacted",
		)

		result = validate_live_trace_fixture(fixture)

		self.assertFalse(result["valid"])
		self.assertIn("user_text", result["unknown_field_violations"])
		self.assertIn("user_text", result["schema_violations"])

	def test_hash_identifiers_must_not_be_blank_or_redacted(self):
		fixture = build_minimal_redacted_live_trace_fixture(session_id_hash=REDACTED_VALUE)

		result = validate_live_trace_fixture(fixture)

		self.assertFalse(result["valid"])
		self.assertEqual(result["hash_field_violations"], ["session_id_hash"])


	def test_raw_identifier_and_entity_keys_are_redacted_and_invalid_if_raw(self):
		record = build_minimal_redacted_live_trace_fixture(
			session_id="SID-001",
			request_id="REQ-001",
			customer="ACME Ltd",
			vendor="Vendor LLC",
			invoice_id="SINV-0001",
			nested={
				"supplier": "Supplier Inc",
				"items": [{"docname": "SO-0001", "party": "ACME"}],
			},
		)

		raw_result = validate_live_trace_fixture(record)
		redacted = redact_live_trace_record(record)
		redacted_result = validate_live_trace_fixture(redacted)

		self.assertFalse(raw_result["valid"])
		self.assertIn("session_id", raw_result["redaction_violations"])
		self.assertIn("request_id", raw_result["redaction_violations"])
		self.assertIn("customer", raw_result["redaction_violations"])
		self.assertIn("vendor", raw_result["redaction_violations"])
		self.assertIn("invoice_id", raw_result["redaction_violations"])
		self.assertIn("nested.supplier", raw_result["redaction_violations"])
		self.assertIn("nested.items[0].docname", raw_result["redaction_violations"])
		self.assertIn("nested.items[0].party", raw_result["redaction_violations"])
		self.assertNotIn("session_id", redacted)
		self.assertNotIn("request_id", redacted)
		self.assertNotIn("customer", redacted)
		self.assertNotIn("vendor", redacted)
		self.assertNotIn("invoice_id", redacted)
		self.assertNotIn("nested", redacted)
		self.assertTrue(redacted_result["valid"])

	def test_hash_identifier_fields_are_preserved_by_redaction(self):
		record = build_minimal_redacted_live_trace_fixture(
			session_id_hash="sha256:session",
			request_id_hash="sha256:request",
		)

		redacted = redact_live_trace_record(record)

		self.assertEqual(redacted["session_id_hash"], "sha256:session")
		self.assertEqual(redacted["request_id_hash"], "sha256:request")
		self.assertTrue(validate_live_trace_fixture(redacted)["valid"])


	def test_unknown_top_level_field_with_raw_business_text_fails(self):
		fixture = build_minimal_redacted_live_trace_fixture(evidence="Customer ACME invoice SINV-0001 is overdue")

		result = validate_live_trace_fixture(fixture)

		self.assertFalse(result["valid"])
		self.assertEqual(result["unknown_field_violations"], ["evidence"])
		self.assertIn("evidence", result["schema_violations"])

	def test_payload_value_with_raw_business_text_fails_schema(self):
		fixture = build_minimal_redacted_live_trace_fixture(payload={"value": "Vendor LLC balance is 5000"})

		result = validate_live_trace_fixture(fixture)

		self.assertFalse(result["valid"])
		self.assertEqual(result["unknown_field_violations"], ["payload"])

	def test_raw_payload_fails_unless_disallowed_or_redacted(self):
		fixture = build_minimal_redacted_live_trace_fixture(raw_payload={"answer": "ACME owes 12000"})

		result = validate_live_trace_fixture(fixture)

		self.assertFalse(result["valid"])
		self.assertEqual(result["unknown_field_violations"], ["raw_payload"])

	def test_redaction_removes_unknown_fields_into_safe_shape(self):
		fixture = build_minimal_redacted_live_trace_fixture(
			evidence="Customer ACME invoice SINV-0001 is overdue",
			payload={"value": "Vendor LLC balance is 5000"},
			raw_payload={"answer": "ACME owes 12000"},
		)

		redacted = redact_live_trace_record(fixture)

		self.assertNotIn("evidence", redacted)
		self.assertNotIn("payload", redacted)
		self.assertNotIn("raw_payload", redacted)
		self.assertTrue(validate_live_trace_fixture(redacted)["valid"])

	def test_extra_metadata_accepts_safe_scalars_and_rejects_raw_sensitive_values(self):
		safe = build_minimal_redacted_live_trace_fixture(
			extra_metadata={
				"fixture_version": "1",
				"schema_version": "1.0",
				"capture_version": "v1",
				"probe_variant": "success",
				"reviewer_note_classification": "qa_note",
				"attempt": 1,
				"synthetic": True,
			}
		)
		unsafe = build_minimal_redacted_live_trace_fixture(
			extra_metadata={
				"fixture_version": "1",
				"payload": {"value": "Customer ACME invoice SINV-0001"},
				"notes": [{"source": "raw ERP source text"}],
			}
		)
		redacted_unsafe = redact_live_trace_record(unsafe)

		self.assertTrue(validate_live_trace_fixture(safe)["valid"])
		unsafe_result = validate_live_trace_fixture(unsafe)
		self.assertFalse(unsafe_result["valid"])
		self.assertIn("extra_metadata.payload", unsafe_result["schema_violations"])
		self.assertIn("extra_metadata.notes[0].source", unsafe_result["schema_violations"])
		self.assertTrue(validate_live_trace_fixture(redacted_unsafe)["valid"])

	def test_extra_metadata_allowlisted_string_keys_use_strict_patterns_or_enums(self):
		fixture = build_minimal_redacted_live_trace_fixture(
			extra_metadata={
				"probe_variant": "Yoma_Bank",
				"fixture_version": "GlobalTradingLtd",
				"schema_version": "customer_1",
				"capture_version": "vGlobalTrading",
				"reviewer_note_classification": "bank_owner",
			}
		)

		result = validate_live_trace_fixture(fixture)
		redacted = redact_live_trace_record(fixture)
		redacted_result = validate_live_trace_fixture(redacted)

		self.assertFalse(result["valid"])
		self.assertIn("extra_metadata.probe_variant", result["schema_violations"])
		self.assertIn("extra_metadata.fixture_version", result["schema_violations"])
		self.assertIn("extra_metadata.schema_version", result["schema_violations"])
		self.assertIn("extra_metadata.capture_version", result["schema_violations"])
		self.assertIn("extra_metadata.reviewer_note_classification", result["schema_violations"])
		self.assertEqual(redacted["extra_metadata"]["probe_variant"], REDACTED_VALUE)
		self.assertEqual(redacted["extra_metadata"]["fixture_version"], REDACTED_VALUE)
		self.assertEqual(redacted["extra_metadata"]["schema_version"], REDACTED_VALUE)
		self.assertEqual(redacted["extra_metadata"]["capture_version"], REDACTED_VALUE)
		self.assertEqual(redacted["extra_metadata"]["reviewer_note_classification"], REDACTED_VALUE)
		self.assertTrue(redacted_result["valid"])

	def test_extra_metadata_generic_note_and_owner_strings_must_be_redacted(self):
		fixture = build_minimal_redacted_live_trace_fixture(
			extra_metadata={"note": "Yoma Bank", "owner": "Global Trading Ltd"}
		)

		result = validate_live_trace_fixture(fixture)
		redacted = redact_live_trace_record(fixture)
		redacted_result = validate_live_trace_fixture(redacted)

		self.assertFalse(result["valid"])
		self.assertIn("extra_metadata.note", result["schema_violations"])
		self.assertIn("extra_metadata.owner", result["schema_violations"])
		self.assertEqual(redacted["extra_metadata"]["note"], REDACTED_VALUE)
		self.assertEqual(redacted["extra_metadata"]["owner"], REDACTED_VALUE)
		self.assertTrue(redacted_result["valid"])

	def test_extra_metadata_nested_generic_string_must_be_redacted(self):
		fixture = build_minimal_redacted_live_trace_fixture(
			extra_metadata={"nested": {"note": "Yoma Bank"}, "attempt": 1}
		)

		result = validate_live_trace_fixture(fixture)
		redacted = redact_live_trace_record(fixture)
		redacted_result = validate_live_trace_fixture(redacted)

		self.assertFalse(result["valid"])
		self.assertIn("extra_metadata.nested.note", result["schema_violations"])
		self.assertEqual(redacted["extra_metadata"]["nested"]["note"], REDACTED_VALUE)
		self.assertTrue(redacted_result["valid"])

	def test_extra_metadata_generic_numeric_and_bool_require_safe_keys(self):
		fixture = build_minimal_redacted_live_trace_fixture(
			extra_metadata={"attempt": 1, "synthetic": True, "owner_count": 2, "owner_verified": True}
		)

		result = validate_live_trace_fixture(fixture)
		redacted = redact_live_trace_record(fixture)

		self.assertFalse(result["valid"])
		self.assertIn("extra_metadata.owner_count", result["schema_violations"])
		self.assertIn("extra_metadata.owner_verified", result["schema_violations"])
		self.assertEqual(redacted["extra_metadata"]["owner_count"], REDACTED_VALUE)
		self.assertEqual(redacted["extra_metadata"]["owner_verified"], REDACTED_VALUE)
		self.assertTrue(validate_live_trace_fixture(redacted)["valid"])

	def test_storage_policy_keeps_raw_live_traces_out_of_repo(self):
		policy = trace_storage_policy()

		self.assertEqual(policy["schema_and_redaction_protocol"], "repo_governance_doc")
		self.assertEqual(policy["synthetic_redacted_fixture"], "repo_allowed")
		self.assertEqual(policy["raw_live_trace"], "external_secure_archive_only")
		self.assertEqual(policy["unredacted_sensitive_trace"], "not_versioned")


if __name__ == "__main__":
	unittest.main()
