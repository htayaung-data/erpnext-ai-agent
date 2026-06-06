import contextlib
import sys
import types
import unittest

if "frappe" not in sys.modules:
    fake_frappe = types.ModuleType("frappe")
    fake_frappe.local = types.SimpleNamespace(site="unit.test")
    fake_frappe.get_doc = lambda *_args, **_kwargs: None
    fake_frappe.get_traceback = lambda: ""
    fake_frappe.log_error = lambda *_args, **_kwargs: None
    sys.modules["frappe"] = fake_frappe

from ai_assistant_ui.qwen_chat import intent_boundary_contract as ibc
from ai_assistant_ui.qwen_chat import service
from ai_assistant_ui.qwen_chat.intent_boundary_proposal_classifier import build_intent_boundary_proposal
from ai_assistant_ui.qwen_chat.intent_boundary_runtime_evidence import validator_owned_runtime_evidence
from ai_assistant_ui.qwen_chat.intent_boundary_runtime_integration import build_v1_ib_runtime_boundary


class V1IBRuntimeEvidenceProviderTests(unittest.TestCase):
    SAFE_REPORT_PROMPT = "Show EC7H-ITEM-A item sales"
    UNSAFE_MIXED_PROMPT = "Show item sales and tell me whether to discount it"

    def tearDown(self):
        self._clear_validator_owned_registries()

    def _clear_validator_owned_registries(self):
        ibc.VALIDATOR_OWNED_TRUSTED_VERIFIER_REGISTRY.clear()
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY.clear()
        ibc.VALIDATOR_OWNED_SAFETY_PROOF_REGISTRY.clear()
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_REGISTRY.clear()
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_REGISTRY.clear()

    def _runtime_boundary_with_provider(self, message):
        with validator_owned_runtime_evidence(message) as evidence:
            return build_v1_ib_runtime_boundary(message, **evidence)

    def assertBlocked(self, boundary):
        self.assertEqual(boundary.get("authority_decision"), "block")
        self.assertFalse(boundary.get("report_routing_allowed"))
        self.assertNotEqual(boundary.get("required_answer_mode"), "governed_erp_answer")

    def test_safe_factual_report_with_validator_owned_runtime_evidence_can_pass(self):
        boundary = self._runtime_boundary_with_provider(self.SAFE_REPORT_PROMPT)

        self.assertEqual(boundary.get("authority_decision"), "allow_report")
        self.assertTrue(boundary.get("report_routing_allowed"))
        self.assertEqual(boundary.get("validator_status"), "valid")
        self.assertEqual(boundary.get("trace_redaction_status"), "safe")
        self.assertEqual(boundary.get("validator_owned_safety_proof_status"), "passed")
        self.assertEqual(boundary.get("replayed_raw_message_safety_final_decision"), "safe")

    def test_same_safe_factual_report_without_provider_evidence_fails_closed(self):
        boundary = build_v1_ib_runtime_boundary(self.SAFE_REPORT_PROMPT)

        self.assertBlocked(boundary)
        self.assertIn("external_verifier_envelope_missing", boundary.get("deterministic_validator_errors") or [])
        self.assertIn("validator_owned_safety_proof_missing", boundary.get("deterministic_validator_errors") or [])

    def test_stale_provider_evidence_fails_closed_for_current_message(self):
        with validator_owned_runtime_evidence("Show EC7H-SUP-A payable status") as stale_evidence:
            boundary = build_v1_ib_runtime_boundary(self.SAFE_REPORT_PROMPT, **stale_evidence)

        self.assertBlocked(boundary)
        self.assertIn("verifier_envelope_raw_hash_mismatch", boundary.get("deterministic_validator_errors") or [])

    def test_caller_supplied_safety_proof_registry_fails_closed_as_forged_evidence(self):
        with validator_owned_runtime_evidence(self.SAFE_REPORT_PROMPT) as evidence:
            boundary = build_v1_ib_runtime_boundary(
                self.SAFE_REPORT_PROMPT,
                **evidence,
                validator_owned_safety_proof_registry={"forged": {"registry_status": "approved"}},
            )

        self.assertBlocked(boundary)
        self.assertIn(
            "validator_owned_safety_proof_registry_caller_supplied_not_allowed",
            boundary.get("deterministic_validator_errors") or [],
        )

    def test_unsafe_mixed_prompt_with_provider_evidence_still_fails_closed(self):
        boundary = self._runtime_boundary_with_provider(self.UNSAFE_MIXED_PROMPT)

        self.assertBlocked(boundary)
        self.assertIn("validator_owned_safety_proof_business_action_intent", boundary.get("deterministic_validator_errors") or [])
        self.assertEqual(boundary.get("replayed_raw_message_safety_final_decision"), "blocked")

    def test_semantic_safe_output_cannot_authorize_without_provider_evidence(self):
        boundary = build_v1_ib_runtime_boundary(
            self.SAFE_REPORT_PROMPT,
            semantic_backstop={"status": "safe", "authority_effect": "evidence_only"},
        )

        self.assertBlocked(boundary)
        self.assertIn("validator_owned_safety_proof_missing", boundary.get("deterministic_validator_errors") or [])

    def test_proposer_only_evidence_cannot_authorize_without_provider_evidence(self):
        proposal = build_intent_boundary_proposal(self.SAFE_REPORT_PROMPT)
        proposal["report_routing_allowed"] = True
        proposal["authority_decision"] = "allow_report"

        boundary = build_v1_ib_runtime_boundary(
            self.SAFE_REPORT_PROMPT,
            proposal_builder=lambda _message: proposal,
        )

        self.assertBlocked(boundary)
        self.assertIn("external_verifier_envelope_missing", boundary.get("deterministic_validator_errors") or [])

    def test_service_runtime_boundary_helper_uses_validator_owned_provider(self):
        boundary = service._build_v1_ib_runtime_boundary_for_service(self.SAFE_REPORT_PROMPT)

        self.assertEqual(boundary.get("authority_decision"), "allow_report")
        self.assertEqual(boundary.get("validator_owned_safety_proof_status"), "passed")

    def test_service_runtime_boundary_helper_fails_closed_when_provider_missing(self):
        @contextlib.contextmanager
        def missing_provider(_message):
            yield {}

        original_provider = service.validator_owned_runtime_evidence
        try:
            service.validator_owned_runtime_evidence = missing_provider
            boundary = service._build_v1_ib_runtime_boundary_for_service(self.SAFE_REPORT_PROMPT)
        finally:
            service.validator_owned_runtime_evidence = original_provider

        self.assertBlocked(boundary)
        self.assertIn("external_verifier_envelope_missing", boundary.get("deterministic_validator_errors") or [])


if __name__ == "__main__":
    unittest.main()
