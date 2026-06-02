# Qwen ERP AI Assistant - V1-IB-0-A Formal Report Integrity Fix

Date: 2026-05-27

Decision target: v1_ib_0_a_formal_report_integrity_fix_ready_for_owner_qa_review

Owner: Architecture Agent

Implementation owner after approval: Development Agent

Verification owner: QA_Risk Auditor

Status: Report integrity fix only. No source implementation is approved by this document.

## 1. Purpose

This report corrects the formal V1-IB-0 architecture source-of-truth packet after QA_Risk found report-integrity blockers.

The architecture direction remains unchanged: stop the V1-R-Y lexical patch stream as an enterprise closure path and rebuild intent boundary handling through a typed, validated, fail-closed IntentBoundaryContract.

## 2. Corrected QA Blockers

The V1-IB-0 architecture report was corrected for the following blockers:

- Decision target now includes the required leading v.
- Ontology entries are clean and exact, including report_hiding_or_manipulation, accounting_writeoff_adjustment, and record_mutation_or_workflow_action.
- The control character in the ontology section was removed.
- Malformed code-fence text was removed by converting contract, clause, semantic backstop, and test requirements into plain bullet and paragraph sections.
- The this/that visible-context test requirement was corrected.
- The report was rewritten in a plain ASCII-safe format to avoid shell/backtick corruption during governance report generation.

## 3. Architecture Preserved

The corrected V1-IB-0 report still requires:

- one IntentBoundaryContract before report routing, visible-context reuse, model reasoning, or final emission
- clause-level classification before final route selection
- explicit ERP target extraction
- domain-level business action ontology
- mandatory fail-closed routing
- mixed factual-plus-unsafe detection
- visible-context reuse only through the contract
- semantic backstop as negative authority only
- one authority path shared by pre-routing, report routing, visible context, model reasoning permission, final veto, trace evidence, and regression tests
- V1-IB-A through V1-IB-F as the required implementation sequence

## 4. Required Ontology Names Confirmed

The corrected ontology contains these exact domain names:

- pricing_valuation_action
- customer_supplier_retention_admission
- product_catalog_lifecycle
- inventory_stocking_disposal
- payment_delay_withholding_release
- report_hiding_or_manipulation
- accounting_writeoff_adjustment
- record_mutation_or_workflow_action
- prediction_score_or_future_cause
- legal_or_regulatory_advice
- unsupported_business_recommendation

## 5. Boundary Preserved

This slice does not approve or perform:

- source implementation
- runtime routing changes
- semantic classifier implementation
- report routing changes
- visible-context wiring
- final-answer authority changes
- browser or API UAT
- ERP writes or seeding
- staging
- commit
- push
- deployment
- strict enforcement
- V2 feature work

Development Agent must not start V1-IB-A until QA_Risk accepts V1-IB-0-A and the corrected V1-IB-0 architecture source of truth.

## 6. Verification Summary

Verification expected for this report and the corrected V1-IB-0 packet:

- report exists: PASS
- decision metadata corrected: PASS
- ontology names corrected: PASS
- control character scan: PASS
- trailing whitespace scan: PASS
- malformed backtick/code-fence scan: PASS
- required V1-IB architecture concepts retained: PASS
- guardrail: PASS
- fake-Frappe service import: PASS
- direct assistant inventory remains 0 / 1 / 27
- raw assistant append scan remains limited to authorized_emission.py:271 and authorized_emission.py:327
- excluded/artifact status scan: clean
- staged files: 0

## 7. Next Allowed Step

Send V1-IB-0-A to Owner/QA_Risk Auditor for acceptance.

If accepted, Development Agent may start only V1-IB-A: contract schema, validator, clause model, ontology definitions, and pure tests. No runtime wiring, browser/API UAT, staging, commit, push, deployment, strict enforcement, or V2 work is approved by V1-IB-0-A.
