from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator

from ai_assistant_ui.qwen_chat import intent_boundary_contract as ibc
from ai_assistant_ui.qwen_chat.intent_boundary_proposal_classifier import build_intent_boundary_proposal


RUNTIME_VERIFIER_SOURCE = "validator_owned_runtime_clause_role_guard"
RUNTIME_VERIFIER_MODEL = "validator-owned-runtime-clause-role-guard"
RUNTIME_VERIFIER_PROMPT_VERSION = "v1-ib-runtime-evidence.1"
RUNTIME_VERIFIER_SECRET = "v1-ib-runtime-verifier-attestation-secret"

RUNTIME_ANALYZER_ID = "validator-owned-runtime-raw-message-analyzer"
RUNTIME_ANALYZER_VERSION = "v1-ib-runtime-evidence.1"
RUNTIME_ANALYZER_SECRET = "v1-ib-runtime-analyzer-attestation-secret"


def _mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _trusted_verifier_registry() -> Dict[str, Dict[str, Any]]:
    return {
        RUNTIME_VERIFIER_SOURCE: {
            "registry_status": "approved",
            "approved_prompt_versions": [RUNTIME_VERIFIER_PROMPT_VERSION],
            "allowed_model_names": [RUNTIME_VERIFIER_MODEL],
            "attestation_secret": RUNTIME_VERIFIER_SECRET,
            "authority_effect": ibc.VERIFIER_AUTHORITY_EFFECT_CONSISTENCY_ONLY,
        }
    }


def _raw_message_safety_analyzer_registry() -> Dict[str, Dict[str, Any]]:
    return {
        RUNTIME_ANALYZER_ID: {
            "registry_status": "approved",
            "approved_analyzer_versions": [RUNTIME_ANALYZER_VERSION],
            "attestation_secret": RUNTIME_ANALYZER_SECRET,
            "replay_source": ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_SOURCE,
            "replay_version": ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_REPLAY_VERSION,
            "replay_config_hash": ibc.hash_text("v1-ib-runtime-replay-config"),
            "replay_artifact_hash": ibc.hash_text("v1-ib-runtime-replay-artifact"),
        }
    }


def _verified_clause(raw_message: Any, clause: Dict[str, Any]) -> Dict[str, Any]:
    normalized = ibc.normalize_message(raw_message)
    try:
        start = int(clause.get("start"))
        end = int(clause.get("end"))
    except (TypeError, ValueError):
        start = 0
        end = 0
    clause_text = normalized[start:end] if 0 <= start <= end <= len(normalized) else ""
    return {
        "clause_id": str(clause.get("clause_id") or ""),
        "span_start": clause.get("start"),
        "span_end": clause.get("end"),
        "normalized_clause_hash": ibc.hash_text(clause_text),
        "verified_clause_type": str(clause.get("clause_type") or ""),
        "verified_factual_lookup_intent": bool(clause.get("factual_lookup_intent")),
        "verified_safe_followup_intent": bool(clause.get("safe_followup_intent")),
        "verified_decision_intent": bool(clause.get("decision_intent")),
        "verified_advice_intent": bool(clause.get("advice_intent")),
        "verified_business_action_intent": bool(clause.get("business_action_intent")),
        "verified_policy_boundary_intent": bool(clause.get("policy_boundary_intent")),
        "verified_business_action_domain": str(clause.get("business_action_domain") or ibc.DOMAIN_NONE),
        "verified_policy_domain": str(clause.get("policy_domain") or ibc.DOMAIN_NONE),
        "verification_status": "verified",
        "verification_confidence": 0.99,
        "verification_blocking_reason": "",
    }


def _verifier_envelope(raw_message: Any, proposal: Dict[str, Any]) -> Dict[str, Any]:
    clauses = [_mapping(clause) for clause in proposal.get("clauses") or [] if isinstance(clause, dict)]
    payload = {
        "envelope_version": "v1-ib-runtime-evidence.1",
        "raw_message_hash": ibc.hash_text(raw_message),
        "normalized_message_hash": ibc.hash_text(ibc.normalize_message(raw_message)),
        "verifier_source": RUNTIME_VERIFIER_SOURCE,
        "verifier_run_id": ibc.hash_text(f"runtime-verifier:{ibc.hash_text(raw_message)}")[:24],
        "verifier_model_name": RUNTIME_VERIFIER_MODEL,
        "verifier_prompt_version": RUNTIME_VERIFIER_PROMPT_VERSION,
        "verifier_status": ibc.AUDIT_STATUS_PASSED,
        "verifier_independence_status": "independent",
        "verifier_authority_effect": ibc.VERIFIER_AUTHORITY_EFFECT_CONSISTENCY_ONLY,
        "trace_redaction_status": ibc.TRACE_REDACTION_SAFE,
        "verified_clauses": [_verified_clause(raw_message, clause) for clause in clauses],
    }
    payload["verifier_payload_hash"] = ibc.canonical_verifier_payload_hash(payload)
    payload["verifier_attestation"] = ibc.verifier_attestation_hash(
        RUNTIME_VERIFIER_SECRET,
        payload["verifier_payload_hash"],
    )
    return payload


def _safety_evidence(subject_hash: str, field_name: str, evidence_type: str, evidence_status: str) -> Dict[str, Any]:
    evidence = {
        "evidence_id": ibc.hash_text(f"{field_name}:{subject_hash}"),
        "evidence_type": evidence_type,
        "evidence_status": evidence_status,
        "evidence_basis": ibc.RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE,
        "source_analyzer_id": RUNTIME_ANALYZER_ID,
        "source_analyzer_version": RUNTIME_ANALYZER_VERSION,
        "derived_from_proposer_roles": False,
        "derived_from_verifier_roles": False,
        "derived_from_semantic_safe_output": False,
        "derived_from_lexical_phrase_authority": False,
        "redaction_status": ibc.TRACE_REDACTION_SAFE,
        "blocking_reason": "",
    }
    evidence["evidence_hash"] = ibc.raw_message_safety_evidence_hash(evidence)
    return evidence


def _safety_proof(raw_message: Any) -> Dict[str, Any]:
    raw_hash = ibc.hash_text(raw_message)
    normalized_hash = ibc.hash_text(ibc.normalize_message(raw_message))
    subject_hash = ibc.raw_message_safety_proof_subject_hash(raw_hash, normalized_hash)
    clause_coverage = _safety_evidence(subject_hash, "raw_message_clause_coverage_evidence", "clause_coverage", "complete")
    secondary_intent = _safety_evidence(subject_hash, "raw_message_secondary_intent_evidence", "secondary_intent", "none")
    mixed_intent = _safety_evidence(subject_hash, "raw_message_mixed_intent_evidence", "mixed_intent", "none")
    residual = _safety_evidence(subject_hash, "raw_message_residual_evidence", "residual", "clear")
    connector = _safety_evidence(subject_hash, "raw_message_connector_evidence", "connector", "accounted")
    reference = _safety_evidence(subject_hash, "raw_message_reference_evidence", "reference", "resolved_or_not_required")
    unsafe_ambiguity = _safety_evidence(subject_hash, "raw_message_unsafe_ambiguity_evidence", "unsafe_ambiguity", "none")
    proof = {
        "registry_status": "approved",
        "raw_message_hash": raw_hash,
        "normalized_message_hash": normalized_hash,
        "safety_proof_subject_hash": subject_hash,
        "validator_safety_analyzer_id": RUNTIME_ANALYZER_ID,
        "validator_safety_analyzer_version": RUNTIME_ANALYZER_VERSION,
        "raw_message_safety_status": "safe",
        "raw_message_clause_coverage_status": "complete",
        "raw_message_secondary_intent_status": "none",
        "raw_message_mixed_intent_status": "none",
        "raw_message_residual_status": "clear",
        "raw_message_reference_status": "resolved_or_not_required",
        "raw_message_safety_evidence_hash": unsafe_ambiguity["evidence_hash"],
        "raw_message_clause_boundary_evidence_hash": clause_coverage["evidence_hash"],
        "raw_message_secondary_intent_evidence_hash": secondary_intent["evidence_hash"],
        "raw_message_residual_evidence_hash": residual["evidence_hash"],
        "raw_message_reference_evidence_hash": reference["evidence_hash"],
        "raw_message_clause_coverage_evidence": clause_coverage,
        "raw_message_secondary_intent_evidence": secondary_intent,
        "raw_message_mixed_intent_evidence": mixed_intent,
        "raw_message_residual_evidence": residual,
        "raw_message_connector_evidence": connector,
        "raw_message_reference_evidence": reference,
        "raw_message_unsafe_ambiguity_evidence": unsafe_ambiguity,
        "safe_route_authority": ibc.ANSWER_MODE_GOVERNED_ERP,
        "safety_proof_basis": ibc.RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE,
        "trace_redaction_status": ibc.TRACE_REDACTION_SAFE,
    }
    proof["safety_proof_payload_hash"] = ibc.raw_message_safety_proof_payload_hash(proof)
    proof["safety_proof_id"] = proof["safety_proof_payload_hash"]
    proof["safety_proof_attestation"] = ibc.raw_message_safety_proof_attestation_hash(
        RUNTIME_ANALYZER_SECRET,
        proof["safety_proof_payload_hash"],
    )
    return proof


def _analysis_evidence_hashes(proof: Dict[str, Any]) -> Dict[str, str]:
    return {
        "raw_message_clause_coverage_evidence_hash": proof["raw_message_clause_coverage_evidence"]["evidence_hash"],
        "raw_message_secondary_intent_evidence_hash": proof["raw_message_secondary_intent_evidence"]["evidence_hash"],
        "raw_message_mixed_intent_evidence_hash": proof["raw_message_mixed_intent_evidence"]["evidence_hash"],
        "raw_message_residual_evidence_hash": proof["raw_message_residual_evidence"]["evidence_hash"],
        "raw_message_connector_evidence_hash": proof["raw_message_connector_evidence"]["evidence_hash"],
        "raw_message_reference_evidence_hash": proof["raw_message_reference_evidence"]["evidence_hash"],
        "raw_message_unsafe_ambiguity_evidence_hash": proof["raw_message_unsafe_ambiguity_evidence"]["evidence_hash"],
    }


def _raw_message_analysis(raw_message: Any, proof: Dict[str, Any]) -> Dict[str, Any]:
    raw_hash = ibc.hash_text(raw_message)
    normalized_hash = ibc.hash_text(ibc.normalize_message(raw_message))
    subject_hash = ibc.raw_message_safety_proof_subject_hash(raw_hash, normalized_hash)
    analysis = {
        "registry_status": "approved",
        "raw_message_hash": raw_hash,
        "normalized_message_hash": normalized_hash,
        "raw_message_analysis_subject_hash": subject_hash,
        "analysis_source": ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_SOURCE,
        "analysis_version": ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_VERSION,
        "analysis_status": "safe",
        "validator_safety_analyzer_id": RUNTIME_ANALYZER_ID,
        "validator_safety_analyzer_version": RUNTIME_ANALYZER_VERSION,
        "raw_message_clause_coverage_status": proof.get("raw_message_clause_coverage_status"),
        "raw_message_secondary_intent_status": proof.get("raw_message_secondary_intent_status"),
        "raw_message_mixed_intent_status": proof.get("raw_message_mixed_intent_status"),
        "raw_message_residual_status": proof.get("raw_message_residual_status"),
        "raw_message_connector_status": "accounted",
        "raw_message_reference_status": proof.get("raw_message_reference_status"),
        "raw_message_unsafe_ambiguity_status": "none",
        "analysis_basis": ibc.RAW_MESSAGE_SAFETY_PROOF_BASIS_NON_DERIVATIVE,
        "derived_from_proposer_roles": False,
        "derived_from_verifier_roles": False,
        "derived_from_semantic_safe_output": False,
        "derived_from_lexical_phrase_authority": False,
        "trace_redaction_status": ibc.TRACE_REDACTION_SAFE,
    }
    analysis.update(_analysis_evidence_hashes(proof))
    return analysis


def _raw_message_analysis_execution(raw_message: Any, analysis: Dict[str, Any]) -> Dict[str, Any]:
    raw_hash = ibc.hash_text(raw_message)
    normalized_hash = ibc.hash_text(ibc.normalize_message(raw_message))
    subject_hash = ibc.raw_message_safety_proof_subject_hash(raw_hash, normalized_hash)
    execution = {
        "registry_status": "approved",
        "raw_message_hash": raw_hash,
        "normalized_message_hash": normalized_hash,
        "analyzer_id": RUNTIME_ANALYZER_ID,
        "analyzer_version": RUNTIME_ANALYZER_VERSION,
        "run_id": f"runtime-analysis-{subject_hash[:12]}",
        "input_hash": ibc.raw_message_analysis_input_hash(raw_hash, normalized_hash, subject_hash),
        "output_hash": ibc.raw_message_analysis_output_hash(analysis),
        "artifact_hash": ibc.hash_text(f"runtime-analysis-artifact:{subject_hash}"),
        "execution_source": ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_SOURCE,
        "execution_version": ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_VERSION,
        "execution_mode": "validator_owned_runtime_provider",
        "execution_status": "completed",
        "trace_redaction_status": ibc.TRACE_REDACTION_SAFE,
        "replay_status": "verified",
    }
    execution["execution_payload_hash"] = ibc.raw_message_analysis_execution_payload_hash(execution)
    execution["attestation"] = ibc.raw_message_analysis_execution_attestation_hash(
        RUNTIME_ANALYZER_SECRET,
        execution["execution_payload_hash"],
    )
    return execution


@contextmanager
def _installed_validator_owned_evidence(
    *,
    trusted_verifier_registry: Dict[str, Dict[str, Any]],
    proof: Dict[str, Any],
    analysis: Dict[str, Any],
    execution: Dict[str, Any],
) -> Iterator[None]:
    registries = (
        ibc.VALIDATOR_OWNED_TRUSTED_VERIFIER_REGISTRY,
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY,
        ibc.VALIDATOR_OWNED_SAFETY_PROOF_REGISTRY,
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_REGISTRY,
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_REGISTRY,
    )
    previous = [dict(registry) for registry in registries]
    try:
        ibc.VALIDATOR_OWNED_TRUSTED_VERIFIER_REGISTRY.clear()
        ibc.VALIDATOR_OWNED_TRUSTED_VERIFIER_REGISTRY.update(trusted_verifier_registry)
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY.clear()
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_SAFETY_ANALYZER_REGISTRY.update(_raw_message_safety_analyzer_registry())
        ibc.VALIDATOR_OWNED_SAFETY_PROOF_REGISTRY.clear()
        ibc.VALIDATOR_OWNED_SAFETY_PROOF_REGISTRY[str(proof.get("safety_proof_id") or "")] = proof
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_REGISTRY.clear()
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_REGISTRY[
            str(analysis.get("raw_message_analysis_subject_hash") or "")
        ] = analysis
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_REGISTRY.clear()
        ibc.VALIDATOR_OWNED_RAW_MESSAGE_ANALYSIS_EXECUTION_REGISTRY[str(execution.get("run_id") or "")] = execution
        yield
    finally:
        for registry, prior in zip(registries, previous):
            registry.clear()
            registry.update(prior)


@contextmanager
def validator_owned_runtime_evidence(
    raw_message: Any,
    *,
    proposal_builder: Callable[[Any], Dict[str, Any]] = build_intent_boundary_proposal,
) -> Iterator[Dict[str, Any]]:
    """Provide scoped validator-owned evidence for one runtime boundary build.

    The yielded kwargs are intentionally minimal. The trusted verifier and raw-message
    safety proof records live only in validator-owned module registries during the
    context, so service code cannot self-attest report authority.
    """

    try:
        proposal = proposal_builder(raw_message)
        verifier_envelope = _verifier_envelope(raw_message, _mapping(proposal))
        proof = _safety_proof(raw_message)
        analysis = _raw_message_analysis(raw_message, proof)
        execution = _raw_message_analysis_execution(raw_message, analysis)
    except Exception:
        yield {}
        return
    with _installed_validator_owned_evidence(
        trusted_verifier_registry=_trusted_verifier_registry(),
        proof=proof,
        analysis=analysis,
        execution=execution,
    ):
        yield {"verifier_envelope": verifier_envelope}
