# Qwen ERP Overdue Severity Policy Pack

Status: active policy approval pack
Date: 2026-04-10
Scope: define the governed overdue-severity policy pack for customer overdue ratio so the remaining Phase 2 blocked threshold set can be approved and activated later without ad hoc interpretation

## 1. Purpose

This note exists to make the overdue-severity policy explicit, reviewable, and maintainable.

It is not a runtime activation note by itself.

It is the approval pack for the last remaining blocked user-facing risk label in the current Phase 2 KPI registry layer.

## 2. Current State

The current runtime already supports:

1. customer overdue ratio definition
2. customer overdue ratio formula ownership
3. blocked-safe behavior when user-facing overdue labels are not yet approved

The blocked runtime items already exist in governed metadata:

1. threshold set:
   - `customer_overdue_ratio_severity_bands`
2. business rule:
   - `overdue_severity_labels_blocked_until_policy_approved`

Those registry entries are intentionally present but still blocked for user-facing activation.

## 3. Governed Basis

The approved technical basis for overdue severity should remain:

1. KPI:
   - `customer overdue ratio as of date`
2. entity grain:
   - `Customer`
3. time basis:
   - `As of date`
4. source report:
   - `Accounts Receivable Summary`
5. formula basis:
   - `31+ aging buckets total / Outstanding Amount`

Important rule:

1. overdue severity must be a presentation layer on top of the already-governed overdue-ratio metric
2. it must not become a separate hidden formula

## 4. Proposed User-Facing Labels And Bands

The current proposed bands already encoded in the blocked threshold registry are:

1. `stable`
   - overdue ratio `< 0.10`
2. `watch`
   - overdue ratio `>= 0.10` and `< 0.30`
3. `elevated`
   - overdue ratio `>= 0.30` and `< 0.60`
4. `critical`
   - overdue ratio `>= 0.60`

These are the proposed user-facing semantics:

1. `stable`
   - only a small share of outstanding is overdue
2. `watch`
   - overdue share is rising and should be watched
3. `elevated`
   - a material share of outstanding is overdue
4. `critical`
   - most outstanding is overdue

## 5. User-Facing Wording Rules

If finance approves activation, the runtime should follow these wording rules:

1. labels may describe exposure posture, not management advice
2. labels must remain tied to the governed overdue ratio and visible amount basis
3. labels must not silently imply collections action, credit hold, or fraud risk
4. labels must not appear when the underlying overdue-ratio metric is unavailable
5. labels should be presented as bounded policy wording, for example:
   - `Overdue severity is watch based on an overdue ratio of 0.18 as of 2026-04-10.`

Disallowed wording examples:

1. `this customer is dangerous`
2. `this customer should be blocked`
3. `this customer will not pay`

## 6. Activation Decision Rule

This policy pack should be treated as approved only when all of the following are true:

1. finance approves the label names
2. finance approves the numeric bands
3. business approves user-facing wording
4. browser/UAT confirms the labels do not drift into advisory behavior

Until then, runtime behavior should remain:

1. blocked-safe
2. ratio and amount answers allowed
3. severity-label rendering not allowed

## 7. Exact Files To Update On Approval

When finance approves the policy, the activation change should be made in governed metadata, not in Python logic.

Primary files:

1. [business_threshold_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_threshold_registry.json)
   - change `customer_overdue_ratio_severity_bands.activation_state`
   - change `blocked_reason`
   - update band labels or numbers only if policy changed
2. [business_rule_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_rule_registry.json)
   - update `overdue_severity_labels_blocked_until_policy_approved`
   - set user-facing rendering permission according to the approved policy

Do not change unless the business meaning changes:

1. [business_definition_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_definition_registry.json)
2. [governed_formula_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/governed_formula_registry.json)

## 8. Verification Required After Approval

After approval and registry activation:

1. update deterministic threshold tests
2. update governed KPI frontdoor tests if user-facing notes change
3. run live smoke for overdue-ratio definition path
4. run browser/UAT for:
   - `what is overdue ratio`
   - `is this customer overdue`
   - `what is this customer's overdue severity`

## 9. Recommendation

The current recommendation is:

1. keep overdue severity blocked in runtime until explicit approval
2. treat this note as the approval pack for later activation
3. keep all future label or band changes centralized in the threshold and business-rule registries

This preserves enterprise maintainability:

1. definitions stay in one place
2. formula basis stays in one place
3. policy numbers stay in one place
4. runtime code stays generic
