# Qwen ERP NBU Zero-Keyword Enterprise Audit

Date: 2026-05-03  
Status: Open stabilization blocker  
Owner: AI Assistant / NBU stabilization  
Severity: P0 for Phase 4 readiness

## Executive Judgment

The user warning is valid.

The project has strong enterprise foundations: governed registries, artifacts, semantic aliases, NBU contracts, authority boundaries, and an expanding regression matrix. However, the current runtime is not yet enterprise-clean under the repository's own `AGENT_RULES.md`.

The latest browser issue proved that some behavior still depends on runtime lexical interpretation. The customer prompt worked because the wording matched an existing explanation trigger; the supplier prompt initially fell back because a different natural phrase did not activate the same behavior. Even after improving the behavior from phrase-specific to evidence-plus-question-shape, the seam still relies on runtime token logic. That is a bridge, not a production-grade NBU architecture.

No Phase 4 complex-business-question expansion should proceed until these drift classes are remediated or explicitly accepted as temporary with a bounded removal plan.

## Enterprise Standard

Zero tolerance means:

1. no runtime business-routing decisions from `if "term" in text`, token intersections, or business regex bags;
2. no case-by-case phrase patching to satisfy browser examples;
3. no renderer-owned intent or authority decisions;
4. no duplicated runtime trees that can keep stale behavior alive;
5. no user-visible technical language leaked from internal contracts;
6. no "green" release claim when guardrails pass but known keyword seams remain.

Acceptable mechanisms are:

1. governed family/capability registries;
2. ontology concepts;
3. canonical semantic alias registries;
4. structured NBU intent contracts;
5. structured continuation and target-reference contracts;
6. structured authority contracts;
7. structural parsers for explicit document ids, dates, years, numeric limits, and ordinals;
8. renderers that consume contracts and evidence but do not infer user intent.

## Evidence From Current Audit

The official command still passes:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
# Qwen enterprise guardrail audit: PASS
```

But a broader runtime scan found roughly 1,420 candidate lexical seams when excluding the nested duplicate runtime tree. This does not mean all 1,420 are violations, but it proves the current guardrail is too narrow for a zero-keyword production bar.

The server tree also contains a severe duplicate runtime copy problem:

```text
impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/qwen_chat/...
```

The nested duplicate tree contains thousands of files and stale copies of runtime modules. This can cause stale behavior, confuse audits, and force repeated "sync the duplicate copy too" work. It is a structural release risk.

## Findings

### P0: Runtime NBU Classification Still Uses Token / Regex Business Logic

Examples:

```text
qwen_chat/natural_business_understanding_request_classification.py
```

Observed patterns:

```python
tokens.intersection(FRESH_QUERY_VERBS)
tokens.intersection(BUSINESS_OBJECT_TERMS)
tokens.intersection(BUSINESS_METRIC_TERMS)
tokens.intersection(VISIBLE_CONTEXT_TERMS)
```

Why this is not enterprise-clean:

The front-controller still decides fresh query vs visible context from lexical bags. This is the exact class of issue that caused "risky" vs "concerning" behavior to diverge.

Target shape:

The NBU front controller should receive or produce a typed interpretation contract with:

1. `intent_kind`;
2. `target_reference`;
3. `subject_entity_type`;
4. `requested_action`;
5. `requested_authority`;
6. `evidence_request_type`;
7. confidence and blockers.

The runtime should not derive this by token sets inside the control layer.

### P0: Visible Context Renderer Still Owns Intent And Authority Decisions

Examples:

```text
qwen_chat/visible_context_followup_activation.py
```

Observed patterns:

```python
_should_explain_row_signal(message, row)
_visible_followup_authority_intent(message)
tokens.intersection(prediction_terms)
tokens.intersection(recommendation_terms)
tokens.intersection(causal_terms)
```

Why this is not enterprise-clean:

The renderer/activation seam should not decide whether the user is asking for explanation, prediction, recommendation, or causal analysis. It should receive `authority_intent` and `response_mode` from NBU and only render approved evidence.

Target shape:

Move intent and authority classification into a structured NBU `VisibleArtifactIntentContract`.

Renderer inputs should be:

1. resolved artifact;
2. resolved row/entity;
3. evidence profile;
4. approved response mode;
5. authority boundary state.

### P0: Governed Requery Activation Still Uses Lexical Detail Detection

Example:

```text
qwen_chat/natural_business_understanding_governed_requery_activation.py
```

Observed pattern:

```python
_message_requests_entity_detail(raw_message)
tokens.intersection({"tell", "information", "info", "details", "detail"})
tokens.intersection({"rank", "row", "that", "this", "supplier", "customer", "item", "product", "invoice"})
```

Why this is not enterprise-clean:

Broad-detail enrichment is still activated through raw wording. This risks endless synonym fixes: "more details", "profile", "tell me about", "expand", "dig into", etc.

Target shape:

NBU should emit `requested_action = entity_detail_enrichment` with target entity and detail depth. Governed requery activation should only verify capability and evidence, not parse wording.

### P0: Composite Evidence Support Still Uses Regex Business-Intent Gates

Example:

```text
qwen_chat/composite_evidence_support.py
```

Observed pattern:

```python
re.search(r"\b(why|explain|reason|because|breakdown|driver|basis)\b", normalized)
re.search(r"\b(aging|ageing|bucket|buckets|due period|breakdown)\b", normalized)
```

Why this is not enterprise-clean:

Composite evidence decisions should be driven by structured evidence request type, not raw phrase detection.

Target shape:

NBU should emit `evidence_request_type` such as:

1. `row_fact_explanation`;
2. `driver_explanation`;
3. `aging_breakdown`;
4. `policy_boundary`;
5. `prediction_boundary`;
6. `causal_boundary`.

### P0: Duplicate Runtime Tree Is A Release Blocker

Example:

```text
qwen_chat/qwen_chat/
qwen_chat/qwen_chat/qwen_chat/
qwen_chat/qwen_chat/qwen_chat/qwen_chat/
```

Observed impact:

The same stale phrases appeared in nested copies after canonical files were fixed. This forced additional sync and made audits misleading.

Target shape:

1. decide canonical runtime path;
2. delete or archive nested duplicate trees;
3. add a guardrail that fails if nested `qwen_chat/qwen_chat` runtime modules exist;
4. verify imports and app packaging still work.

### P1: Guardrail Audit Is Too Narrow

The existing guardrail catches some phrase logic, but it passed while several runtime token gates remained.

Target shape:

Add a stricter stabilization guardrail profile:

1. fail on runtime `tokens.intersection(...)` in protected NBU/control/rendering files;
2. fail on business-domain regex bags in runtime files;
3. fail on `raw_message` parsing in renderer modules;
4. fail on nested duplicate runtime trees;
5. allow structural parsers by allowlist only: dates, years, document ids, numeric limits, ordinals, markdown parsing, language-script detection.

### P1: Service.py Remains A Regression Amplifier

`qwen_chat/service.py` still owns too much orchestration, compatibility glue, and smoke/probe wrappers.

Target shape:

Continue incremental extraction only after P0 NBU contract seams are stabilized. Do not do a large rewrite.

### P1: Clarification And Fallback Wording Still Has Python-Owned Templates

Some clarification/fallback language is improved, but wording is still partly assembled in Python.

Target shape:

Structured clarification reason contracts plus response metadata should own tone, label, and action choices.

## Immediate Stop Rule

Manual S8 UAT expansion should pause until the NBU keyword drift is addressed.

Do not continue with new business-family coverage or Phase 4 complex business questions while:

1. renderer or activation modules decide intent from raw wording;
2. duplicate runtime trees remain;
3. guardrails do not fail on the known drift classes.

## Recommended Remediation Mini-Phase

### ZK-S0: Freeze And Baseline

1. Record this audit.
2. Capture current branch status and touched files.
3. Confirm canonical runtime path.
4. Stop new feature work.

Exit gate:

1. audit doc committed or staged for commit;
2. no further phrase-fix implementation without contract design.

### ZK-S1: Duplicate Runtime Tree Elimination

1. Inventory nested `qwen_chat/qwen_chat` files.
2. Prove they are not imported by runtime.
3. Archive or remove them from the active app tree.
4. Add guardrail to fail if nested runtime duplication returns.

Exit gate:

1. no nested duplicate runtime modules;
2. app imports and targeted tests pass.

### ZK-S2: NBU Intent Contract Front Door

Create a typed contract for natural business understanding:

1. `intent_kind`;
2. `request_scope`;
3. `target_reference`;
4. `entity_type`;
5. `action_type`;
6. `evidence_request_type`;
7. `authority_request_type`;
8. `presentation_request_type`;
9. confidence and blockers.

Exit gate:

1. visible-context renderer no longer parses `raw_message` for intent;
2. authority boundaries consume contract values only.

### ZK-S3: Visible Context Activation Refactor

Move from message-word checks to contract + artifact evidence:

1. NBU resolves whether the user wants row identity, row explanation, detail enrichment, boundary, or projection.
2. Visible context activation only resolves artifact/row and verifies evidence.
3. Renderer only renders the approved mode.

Exit gate:

1. no `_tokens(raw_message)` in visible-context rendering/authority logic;
2. customer and supplier reason-style tests still pass.

### ZK-S4: Governed Requery / Detail Enrichment Refactor

Replace `_message_requests_entity_detail(raw_message)` with NBU action contract.

Exit gate:

1. "more details" style behavior is not phrase-triggered in requery activation;
2. customer/supplier/item/document detail enrichment tests pass.

### ZK-S5: Stricter Guardrail

Upgrade `check_qwen_enterprise_guardrails.py`.

Exit gate:

1. strict guardrail fails on current drift before fixes;
2. strict guardrail passes only after contract seams are clean;
3. exceptions are allowlisted with comments and tests.

### ZK-S6: Resume S8 Manual UAT

Only after ZK-S1 through ZK-S5 pass.

## Conclusion

The direction is correct, but the implementation is not yet enterprise-clean. The project should not be described as production-ready NBU until the keyword and duplicate-runtime drift are removed structurally.

This audit is now the controlling record for the next stabilization work.

## Progress Update - 2026-05-03

Status: active stabilization, not release-clean yet.

Completed in this slice:

1. strengthened `scripts/check_qwen_enterprise_guardrails.py` so the official guardrail now fails on nested `qwen_chat/qwen_chat` runtime duplication;
2. strengthened the guardrail so protected NBU/control seams fail on token-intersection business routing in:
   - `natural_business_understanding_request_classification.py`;
   - `natural_business_understanding_governed_requery_activation.py`;
   - `visible_context_followup_activation.py`;
3. refactored `visible_context_followup_activation.py` so prediction, recommendation, causal, and explanation handling consumes structured NBU/semantic contracts rather than raw-message token bags;
4. refactored `natural_business_understanding_governed_requery_activation.py` so broad entity-detail enrichment depends on the NBU governed requery plan/candidate contract, not `"more/details/profile"` wording;
5. refactored `natural_business_understanding_request_classification.py` so fresh-business detection uses ontology/semantic-alias signals, while visible-context handling keeps only structural discourse/ordinal handling.

Current automated status before duplicate cleanup:

1. `test_visible_context_followup_activation`: green, 25/25;
2. `test_natural_business_understanding_governed_requery_activation`: green, 10/10;
3. strengthened enterprise guardrail: still red only because nested duplicate runtime tree remains.

Former blocker:

The duplicate runtime tree is verified at:

```text
impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/qwen_chat
```

It was untracked and contained 5,711 files on host and container.

Completed cleanup after explicit user approval:

1. archived the host duplicate runtime tree to:

```text
/home/deploy/erp-projects/erpai_project1/_codex_backups/qwen_chat_duplicate_runtime_tree_20260503.tar.gz
```

2. removed the duplicate tree from the host active app path;
3. removed the duplicate tree from the backend container active app path;
4. verified both active duplicate paths are gone.

Post-cleanup automated status:

1. strengthened enterprise guardrail: green;
2. `test_visible_context_followup_activation`: green, 25/25;
3. `test_natural_business_understanding_governed_requery_activation`: green, 10/10;
4. `ai_assistant_ui.api.get_qwen_sessions`: green after cleanup.

ZK-S1 duplicate runtime tree elimination is complete.
