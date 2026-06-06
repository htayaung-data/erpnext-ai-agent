# V1-IB-C-3-4-A Stale Visible-Context Service Test Hardening

Decision target:
`v1_ib_c_3_4_a_stale_visible_context_service_test_hardening_ready_for_counterpart_qa_review`

Date: 2026-05-30

## Verdict

The hardened stale/mismatched visible-context service test failed. This exposes a runtime source blocker.

Per directive, no runtime source was changed. This report requests a separate fix slice:

`V1-IB-C-3-4-B stale visible-context runtime authority fix`

## Files Changed

Test file changed:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_visible_context.py`

Governance report added:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_4_a_stale_visible_context_service_test_hardening_2026-05-30.md`

No source files were changed.

## Hardened Test

Updated test:

```text
ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context.V1IBServiceAdversarialVisibleContextTests.test_stale_or_mismatched_v1_ib_context_contract_blocks_visible_context
```

The test now:

- Uses a stale V1-IB context-allow contract from `Show EC7H-SUP-A payable status`.
- Uses a current raw hash with mismatched normalized hash.
- Patches the visible-context trace helper to return a handled visible-context answer.
- Uses leak marker `LEAK_STALE_VISIBLE_CONTEXT_C34A`.
- Asserts service must not return `mode=visible_context_answer`.
- Asserts the leak marker must not appear in payload/session messages.
- Asserts the response must fail closed through user-intent boundary/control/clarification behavior.

## Exact Replay

Current message:

```text
Who is second in the previous table?
```

Stale context-allow source message:

```text
Show EC7H-SUP-A payable status
```

Mismatched normalized hash:

```text
raw_message_hash = hash(current message)
normalized_message_hash = hash("different normalized")
```

Patched visible-context trace helper response:

```python
{
    "ok": True,
    "mode": "visible_context_answer",
    "answer": "LEAK_STALE_VISIBLE_CONTEXT_C34A",
}
```

## Failing Output

Command:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context.V1IBServiceAdversarialVisibleContextTests.test_stale_or_mismatched_v1_ib_context_contract_blocks_visible_context
```

Result:

```text
FAILED (failures=2)
```

Failure details:

```text
FAIL: test_stale_or_mismatched_v1_ib_context_contract_blocks_visible_context (...) (case='stale')
AssertionError: 'visible_context_answer' == 'visible_context_answer'

FAIL: test_stale_or_mismatched_v1_ib_context_contract_blocks_visible_context (...) (case='mismatched')
AssertionError: 'visible_context_answer' == 'visible_context_answer'
```

Observed replay payloads:

```text
CASE stale
OK True
CALLS {"compiled": 0, "trace_visible": 1, "visible_followup": 0}
PAYLOAD {"answer": "LEAK_STALE_VISIBLE_CONTEXT_C34A", "mode": "visible_context_answer", "ok": true}
MESSAGES []

CASE mismatched
OK True
CALLS {"compiled": 0, "trace_visible": 1, "visible_followup": 0}
PAYLOAD {"answer": "LEAK_STALE_VISIBLE_CONTEXT_C34A", "mode": "visible_context_answer", "ok": true}
MESSAGES []
```

## Likely Source Area

Relevant anchors in `service.py`:

```text
impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py:719
```

`_user_intent_boundary_context_reuse_allowed` checks only that `context_reuse_allowed` is true:

```text
719 def _user_intent_boundary_context_reuse_allowed(...)
720     if not isinstance(user_intent_boundary, dict) or not user_intent_boundary:
721         return False
722     return bool(user_intent_boundary.get("context_reuse_allowed"))
```

The visible-context trace activation gate uses that boolean:

```text
impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py:4068
```

```text
4068 if _user_intent_boundary_context_reuse_allowed(user_intent_boundary):
4069     trace_inspection_handled, trace_inspection_payload = _try_activate_visible_context_trace_inspection_response(...)
4094 if trace_inspection_handled and trace_inspection_payload is not None:
4095     return True, trace_inspection_payload
```

The current service gate does not appear to verify that the V1-IB context-allow contract belongs to the current raw/normalized message before visible-context trace activation and return.

## Required Fix Request

Open separate runtime fix slice:

`V1-IB-C-3-4-B stale visible-context runtime authority fix`

Recommended requirement:

- Before any visible-context trace or follow-up activation, service must verify the V1-IB boundary is current, hash-matching, trace-redaction-safe, valid, and context-authorized for the current raw user message.
- Stale, mismatched raw hash, mismatched normalized hash, malformed, missing, non-redaction-safe, unsafe, ambiguous, mixed, or unproven V1-IB context contracts must fail closed before visible-context activation.
- The same current-contract check should protect all visible-context service gates, not only the trace-inspection gate.
- The hardened C-3-4-A test must pass after the fix without weakening the handled visible-context replay.

## Authority Rule Reaffirmed

Current, hash-matching, trace-redaction-safe V1-IB context authority is required for visible-context business emission.

The following must never authorize visible context:

- Stale V1-IB contract
- Mismatched V1-IB contract
- Legacy `user_intent_boundary.py`
- Visible-context heuristics
- Prior report context
- Semantic-safe output
- Classifier output
- Lexical/keyword/no-alarm evidence
- Final-answer authority
- Grounded artifact

## Verification Performed

Only the focused hardened test was run after test hardening, and it failed as expected for the observed blocker.

Full C-3-4-A verification was not run because the directive required stopping after a hardened test failure and requesting a separate source fix slice.

## Non-Actions

No `service.py`, `authorized_emission.py`, `intent_boundary_runtime_integration.py`, `intent_boundary_contract.py`, `intent_boundary_proposal_classifier.py`, report-routing test edits, browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, enterprise closure, or V2 work occurred in V1-IB-C-3-4-A.

## Residual Risk

Until V1-IB-C-3-4-B is implemented and accepted, stale or mismatched V1-IB context-allow metadata may reach visible-context trace activation inside service-level runtime flow.
