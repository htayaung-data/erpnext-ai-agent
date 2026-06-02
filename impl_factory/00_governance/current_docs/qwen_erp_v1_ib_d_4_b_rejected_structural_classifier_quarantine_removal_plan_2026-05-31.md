# V1-IB-D-4-B Rejected Structural Classifier Quarantine / Removal Plan

Decision target:
`v1_ib_d_4_b_rejected_structural_classifier_quarantine_removal_plan_ready_for_counterpart_review`

Date: 2026-05-31

## 1. Scope And Boundary

V1-IB-D-4-B is a report-only planning slice. It inventories rejected structural classifier artifacts and defines a future quarantine/removal path so they cannot be confused with accepted V1-IB-B proposal-classifier evidence.

No source, test, runtime, import, deletion, move, rename, quarantine, packaging, staging, commit, push, deployment, browser/API UAT, strict enforcement, release-readiness, or V2 work occurred.

No runtime or test behavior changed. No compatibility fallback was added. No keyword, regex, synonym, punctuation, phrase, or no-alarm authority was added.

## 2. Accepted Authority Model

Accepted V1-IB-B is:

- `intent_boundary_proposal_classifier.py`
- evidence-only
- non-authoritative by itself
- accepted only as proposal evidence for the V1-IB-A/Q validator and contract authority model

Rejected V1-IB-B structural artifacts are not accepted authority:

- `intent_boundary_structural_classifier.py`
- `tests/test_v1_ib_structural_classifier.py`
- the 2026-05-28 deterministic structural classifier reports

No classifier output can authorize routing. Runtime route authority remains only a current, hash-matching, trace-safe, validated V1-IB contract. Lexical, regex, keyword, synonym, punctuation, phrase, and no-alarm logic cannot grant:

- `report_routing_allowed=true`
- `context_reuse_allowed=true`
- `model_reasoning_allowed=true`
- `final_emission_allowed=true`
- `required_answer_mode=governed_erp_answer`
- `authority_decision=allow_report`

## 3. Artifact Inventory

| Artifact | Current git status | Current import/use status | Runtime imports it | Tests import it | Accepted baseline dependency | Can authorize routing | Risk if left in current tree | Proposed future action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_structural_classifier.py` | `??` untracked dirty artifact | Historical rejected classifier module; 674 lines | No runtime import found in `qwen_chat/*.py` static scan | Yes, through `tests/test_v1_ib_structural_classifier.py` | No accepted baseline reference found | No | Could be mistaken for accepted V1-IB-B implementation or reused as lexical/structural authority | Prefer package-safe removal from active source in an approved cleanup/package-refresh branch after dependency tests prove no accepted reliance |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_structural_classifier.py` | `??` untracked dirty artifact | Historical rejected classifier tests; 343 lines | No | Yes, imports rejected classifier at line 22 | No accepted baseline reference found | No | Could be misreported as accepted V1-IB-B test evidence | Remove with rejected source, or move to package-excluded historical archive after QA approval |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md` | `??` untracked dirty artifact | Historical report that states V1-IB-B added a deterministic structural classifier | No | No | No accepted baseline dependency | No | Its title/body may look like accepted V1-IB-B evidence unless labeled rejected | Archive/package-exclude or add future historical/rejected label in approved docs cleanup |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md` | `??` untracked dirty artifact | Historical hardening report after structural-classifier weakness | No | No | No accepted baseline dependency | No | Contains rejected-probe language and may confuse future readers about accepted classifier lineage | Archive/package-exclude with rejected structural classifier reports |
| `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md` | `??` untracked dirty artifact | Historical hardening report for passive-action wording in old structural path | No | No | No accepted baseline dependency | No | Could invite future synonym/phrase patch loops if treated as current evidence | Archive/package-exclude with rejected structural classifier reports |

Current accepted replacement evidence remains:

- `qwen_erp_v1_ib_b_1_proposal_classifier_implementation_boundary_request_2026-05-29.md`
- `qwen_erp_v1_ib_b_proposal_classifier_implementation_2026-05-29.md`
- `qwen_erp_v1_ib_b_a_proposal_classifier_evidence_strictness_fix_2026-05-29.md`
- `qwen_erp_v1_ib_b_b_proposal_classifier_closure_checkpoint_2026-05-29.md`
- `intent_boundary_proposal_classifier.py`
- `tests/test_v1_ib_intent_boundary_proposal_classifier.py`

## 4. Static Import / Reference Scan

Runtime scan:

- `qwen_chat/*.py` runtime references to `intent_boundary_structural_classifier`: none found, excluding the rejected classifier file itself.
- `service.py`: no runtime import of rejected structural classifier.
- `authorized_emission.py`: no runtime import of rejected structural classifier.
- `intent_boundary_runtime_integration.py`: no runtime import of rejected structural classifier.

Test scan:

- `tests/test_v1_ib_structural_classifier.py` imports `intent_boundary_structural_classifier` at line 22.
- `tests/test_v1_ib_d_legacy_restrict_only.py` references `intent_boundary_structural_classifier` only for static non-authority import assertions.
- Accepted baseline modules have no structural-classifier references.

Accepted baseline reference scan:

```text
ACCEPTED_BASELINE_STRUCTURAL_REFERENCES=[]
```

Governance report scan:

- `intent_boundary_structural_classifier` appears in 14 current governance reports.
- The three rejected 2026-05-28 report filenames each appear in 7 current governance reports.
- `structural classifier` appears in 26 current governance reports, including old V1-R/Y lexical/structural hardening history.
- Later V1-IB-B-B/C/D reports repeatedly classify old structural artifacts as rejected historical scratch.

Confusion risk:

- `qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md` contains language such as "V1-IB-B adds a pure deterministic structural classifier" and test pass claims. Without later context, this can be misread as accepted V1-IB-B evidence.
- Accepted V1-IB-B evidence is proposal-classifier evidence-only. The accepted report chain supersedes the rejected structural classifier chain.

## 5. Quarantine Options

### Option A: Delete Rejected Structural Source/Test In Cleanup Branch

Pros:

- Strongest package hygiene.
- Eliminates accidental imports from active source/test directories.
- Makes release review simpler.

Cons:

- Requires explicit cleanup/package branch approval.
- Requires baseline and static import verification before and after deletion.
- Loses easy local access to historical scratch unless reports preserve enough context.

### Option B: Move To Package-Excluded Historical Directory

Pros:

- Preserves forensic history.
- Removes artifacts from active runtime/test directories.
- Makes release packaging exclusion explicit.

Cons:

- Requires move/rename approvals and import-scan verification.
- Historical directories can still confuse future agents if labels are weak.
- Packaging rules must explicitly exclude the archive.

### Option C: Keep In Place But Add Explicit Package-Exclusion/Governance Labels

Pros:

- Lowest immediate risk of breaking imports.
- Useful if cleanup branch is not ready.
- Makes rejection status visible.

Cons:

- Leaves rejected classifier in active source/test directories.
- Continues confusion risk for future agents and package reviewers.
- Enterprise preference disfavors indefinite retention in active paths.

### Option D: Convert Useful Assertions Into Accepted V1-IB Tests, Then Remove Old Files

Pros:

- Preserves any valuable safety intent without preserving rejected implementation.
- Best alignment with accepted V1-IB-A/B/C/D authority model.
- Supports package-safe removal with stronger evidence.

Cons:

- Requires careful bounded test-alignment slices.
- Must avoid importing or legitimizing rejected classifier as route authority.

Recommended primary path:

Use Option D as the evidence-preservation approach, followed by Option A for source/test removal or Option B for package-excluded archival in an approved package-refresh branch.

For governance reports, prefer Option B/C hybrid: keep historical governance records available but clearly label/package-exclude rejected 2026-05-28 structural reports during future docs cleanup. Do not treat them as release evidence.

## 6. Required Future Slice Sequence

No implementation occurs in D-4-B. Future bounded slices should be:

1. `V1-IB-D-4-C legacy lexical tests classification/alignment plan`
   - Report-only.
   - Classify old lexical/user-intent tests and determine whether any useful assertions should be rewritten as accepted V1-IB tests.

2. `V1-IB-D-4-B-1 rejected structural classifier quarantine path decision`
   - Report-only if QA wants a standalone decision before cleanup.
   - Choose deletion versus package-excluded archival.

3. `V1-IB-D-4-B-2 structural classifier independence verification`
   - Tests/static-scan only.
   - Prove accepted baseline and D-level evidence do not depend on rejected structural classifier artifacts.

4. `V1-IB-D-4-B-3 cleanup implementation in package-refresh branch`
   - Implementation only after explicit QA/Counterpart approval.
   - Delete or move rejected source/test artifacts according to the selected path.
   - Do not run in the current dirty worktree by default.

5. `V1-IB-D-4-B-4 post-cleanup verification/report`
   - Verify accepted baseline, D tests, import scans, package exclusion, and governance labels.

## 7. Non-Negotiable Cleanup Rules

- No deletion from the current dirty worktree without explicit cleanup/package branch approval.
- No silent deletion of tests.
- No moving source files without static import scan and baseline verification.
- No replacing rejected structural classifier with a new lexical/regex classifier.
- No treating rejected reports as release evidence.
- No package readiness claim until QA approves cleanup.
- Accepted V1-IB-B proposal classifier must remain evidence-only.
- Cleanup must not change V1-IB authority semantics.

## 8. Recommended Next Step

Audit result:

- No runtime import of rejected structural classifier found.
- No accepted baseline dependency found.
- Only the old structural classifier test imports the rejected module directly.
- D-4-A references the rejected classifier only for non-authority static assertions.

Recommended next step:

`V1-IB-D-4-C legacy lexical tests classification/alignment plan`, report-only.

Reason:
the structural classifier artifacts are clearly rejected/non-runtime. The broader remaining cleanup risk is old lexical/user-intent tests and V1-R/Y hardening history. D-4-C should classify which old tests can be rewritten as V1-IB restrict-only evidence and which should be quarantined or excluded from release evidence.

No D-4-B-A blocker slice is required by this audit unless QA/Counterpart disagrees.

## 9. Verification

| Check | Result |
| --- | --- |
| Report present | PASS: `qwen_erp_v1_ib_d_4_b_rejected_structural_classifier_quarantine_removal_plan_2026-05-31.md` exists |
| Static import/reference scan | PASS: no runtime import; only old structural test imports rejected module; accepted baseline references `[]` |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS: `FAKE_FRAPPE_IMPORT_PASS` |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw assistant append scan | PASS: only `authorized_emission.py:271` and `authorized_emission.py:327` |
| Excluded/artifact scan | PASS: forbidden artifact status count `0` |
| Staged files count | PASS: `0` |
| Dirty worktree count | Recorded: `147` |
| Report hygiene scan | PASS: decision target present; no placeholder verification results remain |

Do not claim D-4 closure or V1-IB-D closure from D-4-B.
