from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Iterable, List

from .natural_business_understanding_contracts import CONTRACT_VERSION


REGRESSION_SUITE_BOUNDARY_CONTRACT_TYPE = "qwen_regression_suite_boundary_contract"
REGRESSION_SUITE_ENTRY_CONTRACT_TYPE = "qwen_regression_suite_entry_contract"

GATE_RELEASE_BLOCKING_CONTRACT = "release_blocking_contract"
GATE_RUNTIME_REQUIRED_SMOKE = "runtime_required_smoke"
GATE_LEGACY_STABILIZATION_BACKLOG = "legacy_stabilization_backlog"
GATE_STALE_EXPECTATION_CLEANUP = "stale_expectation_cleanup"
GATE_EXPLORATORY_OR_MANUAL_UAT = "exploratory_or_manual_uat"

RUNTIME_NONE = "none"
RUNTIME_FRAPPE_SESSION = "frappe_session_runtime"
RUNTIME_BROWSER_MANUAL = "browser_manual"

BLOCKING_RELEASE = "blocks_release"
BLOCKING_RUNTIME = "blocks_runtime_uat"
BLOCKING_BACKLOG = "non_blocking_backlog"
BLOCKING_CLEANUP = "cleanup_required_before_full_discovery_gate"
BLOCKING_MANUAL = "manual_acceptance_required"

STATUS_VERIFIED_PASS = "verified_pass"
STATUS_KNOWN_RED_CLASSIFIED = "known_red_classified"
STATUS_MANUAL_PENDING = "manual_pending"

REQUIRED_SUITE_FIELDS = [
	"suite_id",
	"test_paths",
	"gate_class",
	"runtime_dependency",
	"blocking_level",
	"owner_area",
	"expected_command",
	"pass_criteria",
	"failure_triage_rule",
	"last_verified_status",
	"allowed_skip_reason",
	"related_contracts",
]

RELEASE_BLOCKING_SUITE_IDS = [
	"s7_enterprise_guardrail",
	"s7_model_role_contracts",
	"s7_visible_context_contracts",
	"s7_nbu_contracts",
	"s7_policy_authority_contracts",
	"s7_projection_and_cardinality_contracts",
	"s7_regression_scenario_packs",
	"s7_manual_uat_evidence_contracts",
	"s7_manual_uat_renderer_contracts",
	"s7_manual_uat_workflow_contracts",
	"s7_manual_uat_artifact_export_contracts",
	"s7_manual_uat_evidence_archive_contracts",
	"s7_manual_uat_evidence_import_contracts",
	"s7_manual_uat_capture_template_contracts",
	"s7_manual_uat_evidence_bundle_roundtrip_contracts",
	"s7_manual_uat_sample_fixture_contracts",
	"s7_manual_uat_evidence_promotion_contracts",
	"s7_operator_evidence_mode_capture_template_contracts",
	"s7_manual_uat_real_evidence_intake_contracts",
	"s7_operator_evidence_import_cli_contracts",
	"s7_operator_evidence_bundle_uat_runbook_contracts",
	"s7_browser_batch_resilience_runner_contracts",
	"s7_browser_batch_cli_adapter_contracts",
]

S7_REGRESSION_SUITE_REGISTRY: List[Dict[str, Any]] = [
	{
		"suite_id": "s7_enterprise_guardrail",
		"test_paths": ["scripts/check_qwen_enterprise_guardrails.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "enterprise_guardrails",
		"expected_command": "python3 scripts/check_qwen_enterprise_guardrails.py",
		"pass_criteria": "Guardrail audit returns PASS with exit code 0.",
		"failure_triage_rule": "Stop the slice; guardrail failures are release-blocking until fixed or formally reclassified.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": ["enterprise_guardrail", "no_keyword_mvp_runtime"],
	},
	{
		"suite_id": "s7_model_role_contracts",
		"test_paths": [
			"test_model_role_observability_contracts.py",
			"test_model_role_strict_readiness_contracts.py",
			"test_model_role_coverage_contracts.py",
		],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "model_role_governance",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_observability_contracts.py "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_strict_readiness_contracts.py "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_model_role_coverage_contracts.py"
		),
		"pass_criteria": "All model-role observability, readiness, and coverage tests pass.",
		"failure_triage_rule": "Block release because model-role traceability cannot be trusted.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_model_role_observability_contract",
			"qwen_model_role_strict_readiness_contract",
			"qwen_model_role_coverage_contract",
		],
	},
	{
		"suite_id": "s7_visible_context_contracts",
		"test_paths": [
			"test_visible_context_followup_activation.py",
			"test_visible_context_conversation_regression.py",
			"test_visible_context_trace_inspection.py",
		],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "visible_context_authority",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_followup_activation.py "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_conversation_regression.py "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_visible_context_trace_inspection.py"
		),
		"pass_criteria": "Visible context authority, row/rank, policy boundaries, final authority, and trace inspection pass.",
		"failure_triage_rule": "Block release because visible artifact selection or trace accountability may be unsafe.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"context_frame_contract",
			"semantic_ownership_ledger",
			"final_answer_authority",
			"model_role_coverage",
		],
	},
	{
		"suite_id": "s7_nbu_contracts",
		"test_paths": ["test_natural_business_understanding_*.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "natural_business_understanding",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest discover "
			"-s impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests "
			"-p 'test_natural_business_understanding_*.py'"
		),
		"pass_criteria": "All NBU deterministic contract/regression tests pass.",
		"failure_triage_rule": "Block release because shadow/NBU arbitration could override governed authority.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": ["nbu_shadow_observation", "context_resolution", "governed_requery"],
	},
	{
		"suite_id": "s7_policy_authority_contracts",
		"test_paths": [
			"test_policy_boundary_uniformity_contracts.py",
			"test_final_answer_authority_contracts.py",
			"test_policy_boundary_response_contracts.py",
		],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "policy_and_final_answer_authority",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_policy_boundary_uniformity_contracts.py "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_final_answer_authority_contracts.py "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_policy_boundary_response_contracts.py"
		),
		"pass_criteria": "Prediction, recommendation, cause, and final-authority boundaries remain governed.",
		"failure_triage_rule": "Block release because unsafe business claims may bypass policy or authority preflight.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": ["policy_boundary_uniformity", "final_answer_authority"],
	},
	{
		"suite_id": "s7_projection_and_cardinality_contracts",
		"test_paths": [
			"test_ranking_limit_parser_contracts.py",
			"test_transaction_listing_projection_contracts.py",
			"test_aging_artifact_row_order.py",
		],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "projection_and_cardinality",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_ranking_limit_parser_contracts.py "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_transaction_listing_projection_contracts.py "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_aging_artifact_row_order.py"
		),
		"pass_criteria": "Requested limits, row order, and projection preservation contracts pass.",
		"failure_triage_rule": "Block release because user-requested cardinality or projection can be silently changed.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": ["requested_limit", "projection_preservation", "row_order"],
	},
	{
		"suite_id": "s7_regression_scenario_packs",
		"test_paths": ["test_regression_scenario_packs.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "regression_scenario_packs",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_regression_scenario_packs.py"
		),
		"pass_criteria": "Structured S7 scenario packs, deterministic cross-family scenarios, manual UAT separation, and trace assertions pass.",
		"failure_triage_rule": "Block release because scenario-pack behavior cannot prove authority, policy, row/rank, and model-role coverage across business journeys.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_regression_scenario_pack_contract",
			"qwen_regression_scenario_contract",
			"semantic_ownership_ledger",
			"final_answer_authority",
			"policy_boundary_uniformity",
			"model_role_coverage",
		],
	},
	{
		"suite_id": "s7_manual_uat_evidence_contracts",
		"test_paths": ["test_manual_uat_evidence_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_evidence_governance",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_evidence_contracts.py"
		),
		"pass_criteria": "Manual UAT checklist export, evidence validation, release-summary blocking, and scenario-pack linkage pass.",
		"failure_triage_rule": "Block release because browser/manual UAT cannot prove expected versus observed authority, policy, and model-role evidence.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_checklist_contract",
			"qwen_manual_uat_evidence_contract",
			"qwen_manual_uat_release_summary_contract",
			"qwen_regression_scenario_pack_contract",
			"visible_context_trace",
			"model_role_coverage",
		],
	},
	{
		"suite_id": "s7_manual_uat_renderer_contracts",
		"test_paths": ["test_manual_uat_renderer_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_renderer_governance",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_renderer_contracts.py"
		),
		"pass_criteria": "Manual UAT checklist, evidence, release-summary, and combined Markdown renderers are deterministic and read-only.",
		"failure_triage_rule": "Block release because UAT evidence exists but cannot be rendered for auditable human review without hiding missing or failed evidence.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_checklist_contract",
			"qwen_manual_uat_evidence_contract",
			"qwen_manual_uat_release_summary_contract",
			"qwen_manual_uat_renderer_contract",
		],
	},
	{
		"suite_id": "s7_manual_uat_workflow_contracts",
		"test_paths": ["test_manual_uat_workflow_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_workflow_governance",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_workflow_contracts.py"
		),
		"pass_criteria": "Manual UAT execution workflow, capture requirements, blocked evidence handling, and release summary generation pass.",
		"failure_triage_rule": "Block release because rendered UAT cannot be executed into governed evidence without bypassing trace or model-role capture.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_execution_workflow_contract",
			"qwen_manual_uat_execution_workflow_stage_contract",
			"qwen_manual_uat_checklist_contract",
			"qwen_manual_uat_evidence_contract",
			"qwen_manual_uat_release_summary_contract",
		],
	},
	{
		"suite_id": "s7_manual_uat_artifact_export_contracts",
		"test_paths": ["test_manual_uat_export_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_artifact_export",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_export_contracts.py"
		),
		"pass_criteria": "Manual UAT artifact export contract, Markdown rendering, release-status visibility, and deterministic file writing pass.",
		"failure_triage_rule": "Block release because manual UAT workflow cannot be archived as a governed artifact without losing policy/model-role or blocking evidence.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_artifact_export_contract",
			"qwen_manual_uat_execution_workflow_pack_contract",
			"qwen_manual_uat_checklist_contract",
			"qwen_manual_uat_release_summary_contract",
		],
	},
	{
		"suite_id": "s7_manual_uat_evidence_archive_contracts",
		"test_paths": ["test_manual_uat_archive_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_evidence_archive",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_archive_contracts.py"
		),
		"pass_criteria": "Manual UAT evidence archive import, JSON/Markdown export, release-blocking mismatch handling, and scenario registry linkage pass.",
		"failure_triage_rule": "Block release because manual UAT evidence cannot be archived with governed authority, policy, model-role, and scenario traceability.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_archive_index_contract",
			"qwen_manual_uat_archive_record_contract",
			"qwen_manual_uat_evidence_contract",
			"qwen_manual_uat_release_summary_contract",
			"qwen_regression_scenario_pack_contract",
		],
	},
	{
		"suite_id": "s7_manual_uat_evidence_import_contracts",
		"test_paths": ["test_manual_uat_import_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_evidence_import",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_import_contracts.py"
		),
		"pass_criteria": "Manual UAT capture import, raw evidence hashing, deterministic field normalization, quarantine handling, and archive handoff pass.",
		"failure_triage_rule": "Block release because captured browser evidence cannot safely become governed archive input without deterministic normalization and quarantine controls.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_import_batch_contract",
			"qwen_manual_uat_import_record_contract",
			"qwen_manual_uat_archive_index_contract",
			"qwen_manual_uat_evidence_contract",
			"qwen_regression_scenario_pack_contract",
		],
	},
	{
		"suite_id": "s7_manual_uat_capture_template_contracts",
		"test_paths": ["test_manual_uat_capture_template_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_capture_template",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_capture_template_contracts.py"
		),
		"pass_criteria": "Manual UAT operator capture templates, import-ready JSON skeletons, export embedding, and S7-6I handoff pass.",
		"failure_triage_rule": "Block release because operators cannot capture browser UAT evidence in a deterministic import-ready shape.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_capture_template_pack_contract",
			"qwen_manual_uat_capture_template_contract",
			"qwen_manual_uat_import_batch_contract",
			"qwen_manual_uat_artifact_export_contract",
			"qwen_regression_scenario_pack_contract",
		],
	},
	{
		"suite_id": "s7_manual_uat_evidence_bundle_roundtrip_contracts",
		"test_paths": ["test_manual_uat_bundle_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_evidence_bundle_roundtrip",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_bundle_contracts.py"
		),
		"pass_criteria": "Manual UAT filled capture records roundtrip through import, archive, bundle artifacts, blockers, and raw evidence hashes.",
		"failure_triage_rule": "Block release because manual UAT signoff cannot prove complete import/archive evidence in one governed bundle.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_evidence_bundle_contract",
			"qwen_manual_uat_import_batch_contract",
			"qwen_manual_uat_archive_index_contract",
			"qwen_manual_uat_capture_template_pack_contract",
			"qwen_regression_scenario_pack_contract",
		],
	},
	{
		"suite_id": "s7_manual_uat_sample_fixture_contracts",
		"test_paths": ["test_manual_uat_sample_fixture_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_sample_fixture",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_sample_fixture_contracts.py"
		),
		"pass_criteria": "Manual UAT sample capture records dry-run through import, archive, and bundle while remaining blocked from production release signoff.",
		"failure_triage_rule": "Block release because operators cannot validate the capture/import/archive/bundle path with a governed dry-run before real browser UAT.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_sample_fixture_contract",
			"qwen_manual_uat_evidence_bundle_contract",
			"qwen_manual_uat_import_batch_contract",
			"qwen_manual_uat_archive_index_contract",
			"qwen_manual_uat_capture_template_pack_contract",
		],
	},
	{
		"suite_id": "s7_manual_uat_evidence_promotion_contracts",
		"test_paths": ["test_manual_uat_promotion_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_evidence_promotion",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_promotion_contracts.py"
		),
		"pass_criteria": "Manual UAT evidence promotion classifies sample, operator, and unsafe evidence structurally before release signoff.",
		"failure_triage_rule": "Block release because sample or unsafe evidence could be promoted as production manual UAT signoff.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_evidence_promotion_contract",
			"qwen_manual_uat_evidence_bundle_contract",
			"qwen_manual_uat_sample_fixture_contract",
			"qwen_manual_uat_import_batch_contract",
			"qwen_manual_uat_archive_index_contract",
		],
	},
	{
		"suite_id": "s7_operator_evidence_mode_capture_template_contracts",
		"test_paths": ["test_manual_uat_operator_capture_template_promotion_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_operator_capture_template_promotion",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_operator_capture_template_promotion_contracts.py"
		),
		"pass_criteria": "Operator capture templates include promotion-required evidence mode, release boundary, promotion intent, and attestation fields.",
		"failure_triage_rule": "Block release because operators could capture real UAT evidence that cannot pass the S7-6M promotion boundary by construction.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_capture_template_pack_contract",
			"qwen_manual_uat_capture_template_contract",
			"qwen_manual_uat_evidence_promotion_contract",
			"qwen_manual_uat_evidence_bundle_contract",
		],
	},
	{
		"suite_id": "s7_manual_uat_real_evidence_intake_contracts",
		"test_paths": ["test_manual_uat_real_evidence_intake_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_real_evidence_intake",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_real_evidence_intake_contracts.py"
		),
		"pass_criteria": "Real operator evidence intake composes import, archive, bundle, and promotion contracts without accepting sample fixtures or incomplete operator attestations.",
		"failure_triage_rule": "Block release because real manual UAT evidence could be promoted without complete operator capture, bundle roundtrip, or promotion-boundary proof.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_real_evidence_intake_contract",
			"qwen_manual_uat_capture_template_pack_contract",
			"qwen_manual_uat_import_batch_contract",
			"qwen_manual_uat_archive_index_contract",
			"qwen_manual_uat_evidence_bundle_contract",
			"qwen_manual_uat_evidence_promotion_contract",
			"qwen_manual_uat_sample_fixture_contract",
		],
	},
	{
		"suite_id": "s7_operator_evidence_import_cli_contracts",
		"test_paths": ["test_manual_uat_operator_evidence_cli_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_operator_evidence_import_cli",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_operator_evidence_cli_contracts.py"
		),
		"pass_criteria": "Operator evidence CLI loads capture JSON files, enforces strict expected-scenario boundaries, composes S7-6O, writes artifacts, and returns nonzero exit for blocked evidence.",
		"failure_triage_rule": "Block release because operators could import real manual UAT evidence through an ungoverned or misleading command path.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_operator_evidence_cli_contract",
			"qwen_manual_uat_real_evidence_intake_contract",
			"qwen_manual_uat_capture_template_pack_contract",
			"qwen_manual_uat_evidence_bundle_contract",
			"qwen_manual_uat_evidence_promotion_contract",
			"qwen_manual_uat_sample_fixture_contract",
		],
	},
	{
		"suite_id": "s7_operator_evidence_bundle_uat_runbook_contracts",
		"test_paths": ["test_manual_uat_operator_runbook_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_operator_evidence_runbook",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_operator_runbook_contracts.py"
		),
		"pass_criteria": "Operator runbook includes required evidence-capture steps, S7 contract references, CLI commands, blocker meanings, forbidden actions, and promotion-ready pass criteria.",
		"failure_triage_rule": "Block release because operators could perform manual browser UAT without governed evidence, trace, attestation, or CLI interpretation instructions.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_operator_runbook_contract",
			"qwen_regression_scenario_pack_contract",
			"qwen_manual_uat_capture_template_pack_contract",
			"qwen_manual_uat_operator_evidence_cli_contract",
			"qwen_manual_uat_real_evidence_intake_contract",
			"qwen_manual_uat_evidence_promotion_contract",
		],
	},
	{
		"suite_id": "s7_browser_batch_resilience_runner_contracts",
		"test_paths": ["test_manual_uat_browser_batch_runner_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_browser_batch_resilience",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_browser_batch_runner_contracts.py"
		),
		"pass_criteria": "Browser batch runner classifies per-scenario answer, trace, timeout, retry, cleanup, and promotion eligibility without silently promoting partial evidence.",
		"failure_triage_rule": "Block release because real browser UAT batches could time out, reuse stale traces, or hide incomplete scenarios from strict evidence promotion.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_browser_batch_runner_contract",
			"qwen_regression_scenario_pack_contract",
			"qwen_manual_uat_operator_runbook_contract",
			"qwen_manual_uat_operator_evidence_cli_contract",
			"qwen_manual_uat_real_evidence_intake_contract",
			"qwen_manual_uat_evidence_promotion_contract",
		],
	},
	{
		"suite_id": "s7_browser_batch_cli_adapter_contracts",
		"test_paths": ["test_manual_uat_browser_batch_cli_contracts.py"],
		"gate_class": GATE_RELEASE_BLOCKING_CONTRACT,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_RELEASE,
		"owner_area": "manual_uat_browser_batch_cli_adapter",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest "
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_manual_uat_browser_batch_cli_contracts.py"
		),
		"pass_criteria": "Browser batch CLI adapter selects scenarios, loads browser capture-result JSON, writes S7-6T runner artifacts, exports strict import argv, and blocks partial evidence.",
		"failure_triage_rule": "Block release because operators could run real browser batch evidence without deterministic per-scenario runner artifacts or safe strict-import handoff.",
		"last_verified_status": STATUS_VERIFIED_PASS,
		"allowed_skip_reason": "",
		"related_contracts": [
			"qwen_manual_uat_browser_batch_cli_contract",
			"qwen_manual_uat_browser_batch_runner_contract",
			"qwen_manual_uat_operator_evidence_cli_contract",
			"qwen_manual_uat_real_evidence_intake_contract",
			"qwen_regression_scenario_pack_contract",
		],
	},
	{
		"suite_id": "frappe_live_smoke_suites",
		"test_paths": [
			"test_post_contract_observability_live.py",
			"test_post_contract_state_live.py",
			"test_post_contract_release_gates.py",
		],
		"gate_class": GATE_RUNTIME_REQUIRED_SMOKE,
		"runtime_dependency": RUNTIME_FRAPPE_SESSION,
		"blocking_level": BLOCKING_RUNTIME,
		"owner_area": "live_runtime_smoke",
		"expected_command": "Run inside a real Frappe bench/site context, not plain PYTHONPATH unittest.",
		"pass_criteria": "Live smoke suites pass in bench context with session doctype and frappe.new_doc available.",
		"failure_triage_rule": "Do not classify as deterministic unit failure; rerun in live bench context before release UAT.",
		"last_verified_status": STATUS_KNOWN_RED_CLASSIFIED,
		"allowed_skip_reason": "Plain unittest lacks Frappe session runtime and cannot provide frappe.new_doc.",
		"related_contracts": ["live_observability", "runtime_state", "release_smoke"],
	},
	{
		"suite_id": "semantic_financial_legacy_full_discovery",
		"test_paths": ["test_semantic_financial_resolution.py"],
		"gate_class": GATE_LEGACY_STABILIZATION_BACKLOG,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_BACKLOG,
		"owner_area": "legacy_semantic_financial_resolution",
		"expected_command": (
			"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
			"python3 -m unittest impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_semantic_financial_resolution.py"
		),
		"pass_criteria": "Legacy semantic financial suite must be split and reclassified before becoming a release-blocking S7 gate.",
		"failure_triage_rule": "Track as backlog until each failure is mapped to current contract, stale expectation, or true regression.",
		"last_verified_status": STATUS_KNOWN_RED_CLASSIFIED,
		"allowed_skip_reason": "Known broad legacy suite mixes current contracts with older semantic expectations.",
		"related_contracts": ["fresh_query_interpretation", "compiler", "financial_resolution"],
	},
	{
		"suite_id": "wording_expectation_cleanup",
		"test_paths": ["historical answer-text assertions across regression suites"],
		"gate_class": GATE_STALE_EXPECTATION_CLEANUP,
		"runtime_dependency": RUNTIME_NONE,
		"blocking_level": BLOCKING_CLEANUP,
		"owner_area": "test_expectation_hygiene",
		"expected_command": "Review failing assertion diffs and replace brittle prose assertions with contract-field assertions.",
		"pass_criteria": "Stale wording expectations are updated only when trace/contract behavior is already proven correct.",
		"failure_triage_rule": "Do not patch production wording to satisfy stale tests; update tests to assert governed contracts.",
		"last_verified_status": STATUS_KNOWN_RED_CLASSIFIED,
		"allowed_skip_reason": "Non-blocking only after corresponding structured contract assertions pass.",
		"related_contracts": ["policy_boundary_uniformity", "final_answer_authority", "visible_context_trace"],
	},
	{
		"suite_id": "s7_manual_browser_uat",
		"test_paths": ["manual_chat_prompts"],
		"gate_class": GATE_EXPLORATORY_OR_MANUAL_UAT,
		"runtime_dependency": RUNTIME_BROWSER_MANUAL,
		"blocking_level": BLOCKING_MANUAL,
		"owner_area": "operator_uat",
		"expected_command": "Run approved S7 browser/chat prompt set after deterministic gates pass.",
		"pass_criteria": "Manual prompts produce expected business-natural answers and trace fields.",
		"failure_triage_rule": "Block UAT signoff if manual trace contradicts deterministic contract behavior.",
		"last_verified_status": STATUS_MANUAL_PENDING,
		"allowed_skip_reason": "May be deferred only when no user-facing behavior changed in the slice.",
		"related_contracts": ["context_authority", "policy_boundary", "model_role_coverage"],
	},
]


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_registry(registry: Iterable[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
	out: List[Dict[str, Any]] = []
	for raw_entry in registry or S7_REGRESSION_SUITE_REGISTRY:
		if isinstance(raw_entry, dict):
			out.append(dict(raw_entry))
	return out


def regression_suite_missing_fields(entry: Dict[str, Any]) -> List[str]:
	return [
		field
		for field in REQUIRED_SUITE_FIELDS
		if field not in entry or (field != "allowed_skip_reason" and not entry.get(field))
	]


def build_regression_suite_entry_contract(entry: Dict[str, Any]) -> Dict[str, Any]:
	clean_entry = dict(entry or {})
	missing_fields = regression_suite_missing_fields(clean_entry)
	gate_class = _clean_text(clean_entry.get("gate_class"))
	runtime_dependency = _clean_text(clean_entry.get("runtime_dependency"))
	blocking_level = _clean_text(clean_entry.get("blocking_level"))
	return {
		"type": REGRESSION_SUITE_ENTRY_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"suite_id": _clean_text(clean_entry.get("suite_id")),
		"test_paths": _clean_list(clean_entry.get("test_paths")),
		"gate_class": gate_class,
		"runtime_dependency": runtime_dependency,
		"blocking_level": blocking_level,
		"owner_area": _clean_text(clean_entry.get("owner_area")),
		"expected_command": _clean_text(clean_entry.get("expected_command")),
		"pass_criteria": _clean_text(clean_entry.get("pass_criteria")),
		"failure_triage_rule": _clean_text(clean_entry.get("failure_triage_rule")),
		"last_verified_status": _clean_text(clean_entry.get("last_verified_status")),
		"allowed_skip_reason": _clean_text(clean_entry.get("allowed_skip_reason")),
		"related_contracts": _clean_list(clean_entry.get("related_contracts")),
		"missing_fields": missing_fields,
		"entry_complete": not missing_fields,
		"release_blocking": gate_class == GATE_RELEASE_BLOCKING_CONTRACT and blocking_level == BLOCKING_RELEASE,
		"runtime_required": runtime_dependency != RUNTIME_NONE,
		"requires_manual_uat": gate_class == GATE_EXPLORATORY_OR_MANUAL_UAT,
	}


def build_regression_suite_boundary_contract(
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	contract_owner: str = "s7_regression_suite_governance",
) -> Dict[str, Any]:
	entries = [build_regression_suite_entry_contract(entry) for entry in _clean_registry(registry)]
	suite_ids = [_clean_text(entry.get("suite_id")) for entry in entries if _clean_text(entry.get("suite_id"))]
	duplicate_suite_ids = sorted({suite_id for suite_id in suite_ids if suite_ids.count(suite_id) > 1})
	missing_release_blocking = [
		suite_id
		for suite_id in RELEASE_BLOCKING_SUITE_IDS
		if suite_id not in suite_ids
	]
	incomplete_entries = [
		_clean_text(entry.get("suite_id")) or "unknown"
		for entry in entries
		if not bool(entry.get("entry_complete"))
	]
	gate_counts: Dict[str, int] = {}
	for entry in entries:
		gate_class = _clean_text(entry.get("gate_class")) or "unknown"
		gate_counts[gate_class] = gate_counts.get(gate_class, 0) + 1
	release_blocking_suites = [
		_clean_text(entry.get("suite_id"))
		for entry in entries
		if bool(entry.get("release_blocking"))
	]
	runtime_required_suites = [
		_clean_text(entry.get("suite_id"))
		for entry in entries
		if bool(entry.get("runtime_required"))
	]
	manual_uat_suites = [
		_clean_text(entry.get("suite_id"))
		for entry in entries
		if bool(entry.get("requires_manual_uat"))
	]
	contract_complete = not duplicate_suite_ids and not missing_release_blocking and not incomplete_entries
	return {
		"type": REGRESSION_SUITE_BOUNDARY_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"contract_complete": bool(contract_complete),
		"release_blocking_gate_defined": bool(release_blocking_suites),
		"suite_count": len(entries),
		"release_blocking_suite_count": len(release_blocking_suites),
		"runtime_required_suite_count": len(runtime_required_suites),
		"manual_uat_suite_count": len(manual_uat_suites),
		"gate_counts": gate_counts,
		"release_blocking_suites": release_blocking_suites,
		"runtime_required_suites": runtime_required_suites,
		"manual_uat_suites": manual_uat_suites,
		"known_red_classified_suites": [
			_clean_text(entry.get("suite_id"))
			for entry in entries
			if _clean_text(entry.get("last_verified_status")) == STATUS_KNOWN_RED_CLASSIFIED
		],
		"missing_release_blocking_suites": missing_release_blocking,
		"duplicate_suite_ids": duplicate_suite_ids,
		"incomplete_entries": incomplete_entries,
		"entries": entries,
		"created_at": _utc_now(),
	}


def release_blocking_regression_commands(
	registry: Iterable[Dict[str, Any]] | None = None,
) -> List[str]:
	commands: List[str] = []
	for entry in build_regression_suite_boundary_contract(registry=registry).get("entries", []):
		if bool(entry.get("release_blocking")):
			commands.append(_clean_text(entry.get("expected_command")))
	return [command for command in commands if command]
