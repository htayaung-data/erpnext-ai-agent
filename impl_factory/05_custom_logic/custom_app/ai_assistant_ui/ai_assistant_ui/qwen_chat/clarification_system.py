"""
Enterprise Clarification System (AI-First, Hybrid Approach)

This module generates contextual clarification questions when:
1. Follow-up intent is ambiguous
2. Requested transformation cannot be executed
3. User request needs confirmation before execution

Enterprise Principle:
- AI-first: Let Qwen generate natural clarifications
- Template fallback: Use templates only if AI fails
- Metadata-driven: Templates in JSON, not code
- Learning: Log unknown scenarios for future improvement
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

try:
    import frappe
except Exception:
    frappe = None

from ai_assistant_ui.qwen_chat.model_backed_helper_metadata import (
    attach_helper_metadata_to_agent_meta,
    build_model_backed_helper_runtime_metadata_bundle,
    build_not_applicable_helper_runtime_metadata_bundle,
)
from ai_assistant_ui.qwen_chat.runtime_client import call_qwen_runtime_chat


# Cache for registry
_registry_cache: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ClarificationQuestion:
    """
    A clarification question to ask the user.
    
    Attributes:
        question: The clarification question text
        options: Suggested options for the user to choose from
        context_type: Type of clarification needed (followup, scope, confirmation)
        generation_method: How this was generated ("ai" or "template")
    """
    question: str
    options: List[str]
    context_type: str  # "followup", "scope", "confirmation", "missing_info"
    generation_method: str = "ai"  # "ai" or "template"
    agent_meta: Dict[str, Any] = field(default_factory=dict)
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to tool payload for UI display."""
        agent_meta = dict(self.agent_meta or {})
        if not agent_meta.get("runtime_metadata_envelope"):
            if self.generation_method == "ai":
                metadata_bundle = build_model_backed_helper_runtime_metadata_bundle(
                    lane_id="clarification_system_ai_generation",
                    role_owner="clarification_system",
                    agent_meta=agent_meta,
                    runtime_source="clarification_generation_without_runtime_agent_meta",
                    answer_mode="clarification_generation",
                    evidence_scope="clarification_question",
                    authority_source="clarification_runtime",
                    preflight_status="passed",
                    fallback_used=True,
                    fallback_reason="missing_runtime_agent_meta",
                )
            else:
                metadata_bundle = build_not_applicable_helper_runtime_metadata_bundle(
                    lane_id="clarification_system_template_fallback",
                    role_owner="clarification_system",
                    runtime_source="clarification_template_fallback",
                    answer_mode="clarification_template",
                    fallback_reason=self.generation_method,
                )
            agent_meta = attach_helper_metadata_to_agent_meta(agent_meta, metadata_bundle)
        else:
            metadata_bundle = {
                "model_role_observability": dict(agent_meta.get("model_role_observability") or {}),
                "model_role_strict_readiness": dict(agent_meta.get("model_role_strict_readiness") or {}),
                "runtime_metadata_envelope": dict(agent_meta.get("runtime_metadata_envelope") or {}),
            }
        return {
            "type": "qwen_clarification_question",
            "question": self.question,
            "options": self.options,
            "context_type": self.context_type,
            "generation_method": self.generation_method,
            "agent_meta": agent_meta,
            "model_role_observability": metadata_bundle["model_role_observability"],
            "model_role_strict_readiness": metadata_bundle["model_role_strict_readiness"],
            "runtime_metadata_envelope": metadata_bundle["runtime_metadata_envelope"],
        }


def _get_registry_path() -> str:
    """Get path to clarification templates registry."""
    possible_paths = [
        "/home/frappe/frappe-bench/qwen_enterprise_metadata/clarification_templates_registry.json",
        "/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/clarification_templates_registry.json",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return possible_paths[0]


def _load_registry() -> Dict[str, Any]:
    """Load clarification templates from metadata."""
    global _registry_cache
    
    if _registry_cache is not None:
        return _registry_cache
    
    try:
        registry_path = _get_registry_path()
        with open(registry_path, 'r', encoding='utf-8') as f:
            _registry_cache = json.load(f)
        return _registry_cache
    except Exception as e:
        if frappe:
            frappe.log_error(
                title="Clarification Registry Load Error",
                message=f"Failed to load: {str(e)}"
            )
        return {
            "contract_version": "1.0",
            "followup_clarification_templates": [],
            "generic_followup_template": {},
            "scope_clarification_templates": [],
            "ambiguous_request_templates": [],
            "metric_labels": {},
            "family_labels": {},
        }


def generate_ai_clarification(
    request_id: str,
    session_id: str,
    user_id: str,
    site_name: str,
    raw_message: str,
    context: Dict[str, Any],
) -> Optional[ClarificationQuestion]:
    """
    Generate clarification using AI (Qwen runtime).
    
    This is the PRIMARY method - AI-first approach.
    
    Args:
        request_id: Request identifier
        session_id: Session identifier
        user_id: User identifier
        site_name: Site name
        raw_message: Original user message
        context: Context information (prior conversation, detected intent, etc.)
    
    Returns:
        ClarificationQuestion or None if AI fails
    """
    # Build AI prompt for clarification generation
    system_prompt = """You are an ERP business assistant. When a user's request is ambiguous or cannot be executed confidently, generate a natural clarification question.

Rules:
1. Be conversational and helpful
2. Reference the prior context when available
3. Offer 2-3 clear options for the user to choose from
4. Keep it concise (1-2 sentences max)
5. Never expose technical internals (capabilities, families, etc.)

Example good clarifications:
- "I want to make sure I show you the right data. Are you asking to add Quantity column to the product ranking above?"
- "Let me clarify: Do you want to see this for a different time period, or with different metrics?"
- "I can help with that. Could you tell me which specific products or time period you're interested in?"

Example bad clarifications:
- "Ambiguous capability candidates: sales_read, product_performance_read" (too technical)
- "I could not complete a grounded ERP lookup" (not helpful)
"""

    # Build context for AI
    context_text = _format_context_for_ai(context)
    
    user_prompt = f"""User's follow-up message: "{raw_message}"

Prior context:
{context_text}

Generate a natural clarification question to confirm what the user wants. Include 2-3 suggested options they can choose from.

Return ONLY a JSON object with this structure:
{{
  "question": "your clarification question",
  "options": ["option 1", "option 2", "option 3"],
  "context_type": "followup" or "scope" or "confirmation" or "missing_info"
}}
"""

    try:
        runtime_payload = call_qwen_runtime_chat(
            session_id=session_id,
            user_id=user_id,
            site_name=site_name,
            message=user_prompt,
            recent_messages=[],
            response_policy={},
            family_tool_context={},
            mode="clarification_generation",
            compiled_query={},
            artifact_context={"system_prompt": system_prompt},
            request_id=request_id,
        )
        
        if not runtime_payload.get("ok"):
            return None
        
        # Parse AI response
        answer_text = runtime_payload.get("answer_text", "").strip()
        
        # Try to extract JSON from response
        clarification_data = _extract_json_from_response(answer_text)
        
        if not clarification_data:
            return None
        
        question = clarification_data.get("question", "").strip()
        options = clarification_data.get("options", [])
        context_type = clarification_data.get("context_type", "followup")
        
        if not question:
            return None
        
        # Ensure we have at least one option
        if not options:
            options = ["Continue", "Let me clarify"]
        
        agent_meta = runtime_payload.get("agent_meta") if isinstance(runtime_payload.get("agent_meta"), dict) else {}
        metadata_bundle = build_model_backed_helper_runtime_metadata_bundle(
            lane_id="clarification_system_ai_generation",
            role_owner="clarification_system",
            agent_meta=agent_meta,
            runtime_source="clarification_generation_runtime_agent_meta" if agent_meta else "clarification_generation_without_runtime_agent_meta",
            answer_mode="clarification_generation",
            evidence_scope="clarification_question",
            authority_source="clarification_runtime",
            preflight_status="passed",
            fallback_used=False,
        )
        agent_meta = attach_helper_metadata_to_agent_meta(agent_meta, metadata_bundle)
        return ClarificationQuestion(
            question=question,
            options=options,
            context_type=context_type,
            generation_method="ai",
            agent_meta=agent_meta,
        )
        
    except Exception as e:
        if frappe:
            frappe.log_error(
                title="AI Clarification Generation Error",
                message=f"Failed to generate AI clarification: {str(e)}"
            )
        return None


def generate_template_clarification(
    raw_message: str,
    family_id: str,
    detected_modes: List[str],
    requested_columns: List[str],
    target_metric: str,
    governance_status: str = "",
    concept_id: str = "",
) -> Optional[ClarificationQuestion]:
    """
    Generate clarification using templates (fallback method).
    
    This is the FALLBACK - used only if AI fails.
    
    Args:
        raw_message: Original user message
        family_id: Current family context
        detected_modes: Detected follow-up modes
        requested_columns: Requested columns
        target_metric: Target metric if detected
        governance_status: For scope clarifications
        concept_id: For scope clarifications
    
    Returns:
        ClarificationQuestion or None
    """
    registry = _load_registry()
    
    # Try follow-up templates
    if detected_modes:
        templates = registry.get("followup_clarification_templates", [])
        for mode in detected_modes:
            template_data = next((t for t in templates if t.get("mode") == mode), None)
            if template_data:
                return _format_template_clarification(template_data, {
                    "columns_text": ", ".join(requested_columns) if requested_columns else "additional columns",
                    "family_label": _get_label(family_id, registry.get("family_labels", {})),
                    "metric_label": _get_label(target_metric, registry.get("metric_labels", {})),
                })
        
        # Generic follow-up template
        generic = registry.get("generic_followup_template", {})
        if generic:
            return _format_template_clarification(generic, {
                "modes_text": " or ".join(detected_modes).replace("_", " "),
            })
    
    # Try scope templates
    if governance_status:
        templates = registry.get("scope_clarification_templates", [])
        template_data = next((t for t in templates if t.get("governance_status") == governance_status), None)
        if template_data:
            return _format_template_clarification(template_data, {
                "concept_label": _get_label(concept_id, registry.get("family_labels", {})),
            })
    
    return None


def generate_clarification(
    request_id: str,
    session_id: str,
    user_id: str,
    site_name: str,
    raw_message: str,
    context: Dict[str, Any],
    use_ai_first: bool = True,
) -> ClarificationQuestion:
    """
    Generate clarification using hybrid approach.
    
    Strategy:
    1. Try AI first (if use_ai_first=True)
    2. If AI fails, fall back to templates
    3. If templates fail, return generic clarification
    
    Args:
        request_id: Request identifier
        session_id: Session identifier
        user_id: User identifier
        site_name: Site name
        raw_message: Original user message
        context: Context information
        use_ai_first: Whether to try AI first (default: True)
    
    Returns:
        ClarificationQuestion (always returns something, never None)
    """
    clarification = None
    
    # Step 1: Try AI first
    if use_ai_first:
        clarification = generate_ai_clarification(
            request_id=request_id,
            session_id=session_id,
            user_id=user_id,
            site_name=site_name,
            raw_message=raw_message,
            context=context,
        )
        
        # Log AI success/failure
        if frappe:
            if clarification:
                frappe.log_error(
                    title="Clarification: AI Success",
                    message=f"Request: {raw_message}\nQuestion: {clarification.question[:100]}"
                )
            else:
                frappe.log_error(
                    title="Clarification: AI Failed, Using Template",
                    message=f"Request: {raw_message}\nFalling back to template"
                )
    
    # Step 2: Fall back to templates
    if not clarification:
        clarification = generate_template_clarification(
            raw_message=raw_message,
            family_id=context.get("family_id", ""),
            detected_modes=context.get("detected_modes", []),
            requested_columns=context.get("requested_columns", []),
            target_metric=context.get("target_metric", ""),
            governance_status=context.get("governance_status", ""),
            concept_id=context.get("concept_id", ""),
        )
    
    # Step 3: Generic fallback
    if not clarification:
        clarification = ClarificationQuestion(
            question="I want to make sure I understand correctly. Could you clarify what you need?",
            options=["Let me rephrase", "Show me what you can do", "Help"],
            context_type="missing_info",
            generation_method="fallback"
        )
    
    return clarification


def _format_context_for_ai(context: Dict[str, Any]) -> str:
    """Format context information for AI consumption."""
    lines = []
    
    if context.get("family_id"):
        lines.append(f"- Current context: {context.get('family_id', 'unknown')}")
    
    if context.get("prior_query"):
        lines.append(f"- Prior query: {context.get('prior_query', '')[:100]}")
    
    if context.get("detected_modes"):
        lines.append(f"- Detected intent: {', '.join(context.get('detected_modes', []))}")
    
    if context.get("requested_columns"):
        lines.append(f"- Requested columns: {', '.join(context.get('requested_columns', []))}")
    
    if context.get("target_metric"):
        lines.append(f"- Target metric: {context.get('target_metric', '')}")

    if context.get("governance_status"):
        lines.append(f"- Governance status: {context.get('governance_status', '')}")
    
    return "\n".join(lines) if lines else "- No prior context available"


def _extract_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON object from AI response text."""
    import re
    
    # Try to find JSON object in response
    json_match = re.search(r'\{[^{}]*"question"[^{}]*\}', text, re.DOTALL)
    
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Try parsing entire text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    return None


def _format_template_clarification(template_data: Dict[str, Any], context: Dict[str, Any]) -> Optional[ClarificationQuestion]:
    """Format a template clarification."""
    template = template_data.get("template", "")
    options = template_data.get("options", [])
    context_type = template_data.get("context_type", "confirmation")
    
    # Format template
    try:
        question = template.format(**context)
    except KeyError:
        question = template  # Use as-is if formatting fails
    
    # Format options
    formatted_options = []
    for opt in options:
        try:
            formatted_options.append(opt.format(**context))
        except KeyError:
            formatted_options.append(opt)
    
    if not formatted_options:
        formatted_options = ["Continue", "Revise"]
    
    return ClarificationQuestion(
        question=question,
        options=formatted_options,
        context_type=context_type,
        generation_method="template"
    )


def _get_label(key: str, labels_dict: Dict[str, str]) -> str:
    """Get human-readable label from dictionary."""
    if not key:
        return ""
    return labels_dict.get(key, key.replace("_", " ").title())


def build_clarification_response(
    clarification: ClarificationQuestion,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build full clarification response for the user."""
    clarification_payload = clarification.to_payload()
    metadata_bundle = {
        "model_role_observability": dict(clarification_payload.get("model_role_observability") or {}),
        "model_role_strict_readiness": dict(clarification_payload.get("model_role_strict_readiness") or {}),
        "runtime_metadata_envelope": dict(clarification_payload.get("runtime_metadata_envelope") or {}),
    }
    agent_meta = {
        "engine": "clarification_system",
        "context_type": clarification.context_type,
        "generation_method": clarification.generation_method,
        "hybrid_approach": True,
        **metadata_bundle,
    }
    return {
        "ok": True,
        "answer_text": clarification.question,
        "clarification": clarification_payload,
        "agent_meta": agent_meta,
        "model_role_observability": metadata_bundle["model_role_observability"],
        "model_role_strict_readiness": metadata_bundle["model_role_strict_readiness"],
        "runtime_metadata_envelope": metadata_bundle["runtime_metadata_envelope"],
    }


def reload_registry() -> None:
    """Reload the registry from disk."""
    global _registry_cache
    _registry_cache = None
    _load_registry()
