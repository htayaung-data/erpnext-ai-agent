# Qwen ERP Phase 3.4 Customer Risk-As-Of Composite Design

Status: `3.4A` design lock complete, `3.4B` contract slice complete, `3.4C` assembly support complete, `3.4D` ranking release complete, `3.4E` detail/follow-up closure complete, `3.4F` nex
Date: 2026-04-27
Scope: Enterprise design lock for the customer-risk-as-of composite archetype

## 1. Decision

Phase `3.4` will activate customer risk as a governed composite artifact, not as a prompt keyword, ad hoc score, or one-off report handler.

The approved archetype is:

1. customer grain
2. as-of date aligned across all component metrics
3. overdue amount as the primary ranking basis
4. overdue ratio, outstanding amount, and credit utilization as supporting risk contex
5. threshold filtering only where threshold policy is active and user-facing labels are approved
6. safe degradation when a component metric cannot be proven for a row

This means user asks such as `show risky customers`, `show overdue customers with credit usage`, and `which customers are highest risk as of today` should eventually resolve through one reusable customer-risk-as-of family contract.

They must not become separate keyword branches.

## 2. Why This Is The Correct Next Slice

The project already has the required lower-level ingredients:

1. governed business definitions for customer overdue ratio and customer credit utilization
2. governed KPI execution entries for customer as-of scalar and ranking shapes
3. business rules for credit-utilization basis and blocked overdue severity labels
4. threshold metadata for credit utilization and overdue ratio
5. composite artifact contracts and assembly concepts from Phase `3.1` to `3.3`
6. customer detail and follow-up context support from the governed scope and conversation-control work

So Phase `3.4` should not invent a new risk engine.

It should compose already governed pieces into a reusable risk-as-of artifact.

## 3. Approved Business Meaning

`customer_risk_as_of` means:

1. open customer exposure and overdue condition as of a governed report date
2. ranked primarily by overdue amount unless the user explicitly asks for another approved basis
3. supported by outstanding amount, overdue ratio, and credit utilization where those values are available
4. presented as business evidence for credit and collection review

It does not mean:

1. predicted default probability
2. payment-behavior forecasting
3. automatic collection recommendation
4. credit-limit approval or rejection
5. moral labeling such as `bad customer`
6. unapproved severity labels for overdue bands
7. a hidden weighted risk score

## 4. Component Metrics

The initial family may use these component metrics only if the registry and runtime execution prove them available:

1. `outstanding_amount`
   - customer open balance as of the report date
   - used as exposure context and denominator for overdue ratio
2. `overdue_amount`
   - customer overdue open amount as of the report date
   - primary ranking basis for the default risk view
3. `customer_overdue_ratio`
   - overdue amount divided by outstanding amoun
   - semantic basis already exists as `customer_overdue_ratio_as_of_date`
4. `customer_credit_utilization`
   - outstanding amount divided by configured customer credit limi
   - semantic basis already exists as `credit_utilization_customer_as_of_date`
5. `credit_limit`
   - configured customer credit limi
   - used only as support for utilization and credit-limit status
6. `aging_buckets`
   - bucket breakdown used to explain overdue exposure
   - must stay aligned to the same as-of date

Optional context fields may be shown when already present in governed customer detail or ranking evidence:

1. customer name
2. territory or region
3. latest invoice date
4. invoice coun
5. total due
6. available credi

Optional context fields are not allowed to become hidden ranking basis unless approved in the family metadata.

## 5. Default Variation Policy

The default variation for a broad risk ask should be:

1. family: `customer_risk_as_of`
2. primary metric: overdue amoun
3. supporting metrics: outstanding amount, overdue ratio, credit utilization
4. date basis: explicit user as-of date, otherwise current governed report date
5. row limit: existing governed default list limit unless user asks for a different supported limi
6. sort: descending by overdue amoun

If the user explicitly asks for credit usage, utilization, over-limit customers, or credit-limit pressure, the family may switch primary basis to credit utilization only after `3.4B` declares that variation in metadata.

If the user asks for overdue severity labels, the system must respect the active rule that overdue severity labels are blocked until policy approval.

## 6. Compatibility Rules

All component metrics in a customer-risk-as-of artifact must satisfy:

1. same company scope
2. same customer grain
3. same as-of date
4. compatible open-balance source basis
5. row identity based on governed customer identity, not display-name similarity
6. explicit missing-component policy

Rows may degrade safely when:

1. credit limit is missing
2. utilization denominator is zero or unavailable
3. a supporting metric cannot be proven for the same as-of date

Rows must not silently fabricate:

1. credit utilization
2. overdue ratio
3. severity band
4. payment risk score
5. collection recommendation

## 7. Clarification And Fallback Policy

The assistant should clarify when:

1. the user asks for `risk` but the requested basis is not clear and no approved default variation applies
2. the user asks for a blocked risk concept such as prediction, recommendation, or severity label
3. the user requests a metric whose source cannot be proven inside the customer-risk-as-of family

The assistant should answer directly when:

1. the broad customer-risk ask maps to the approved default variation
2. the user asks for overdue customers and the overdue basis is available
3. the user asks for credit utilization and the utilization variation is approved
4. the user follows up from a customer-risk result to customer detail using a row from the same artifac

Fallback wording must stay business-natural:

1. explain what governed evidence is missing
2. offer the closest supported customer-risk view
3. avoid internal contract names unless the user asks for technical detail

## 8. Runtime Contract Target For 3.4B

`3.4B` should add or extend metadata/contracts so the runtime can resolve:

1. `family_id`: `customer_risk_as_of`
2. `composite_kind`: `as_of_customer_risk_ranking`
3. `entity_grain`: `customer`
4. `time_scope_type`: `as_of_date`
5. `default_primary_metric`: `overdue_amount`
6. `supporting_metrics`: `outstanding_amount`, `customer_overdue_ratio`, `customer_credit_utilization`
7. `default_sort`: descending by overdue amoun
8. `missing_component_policy`: safe row degradation
9. `blocked_variations`: predictive risk, recommendations, unapproved overdue severity labels
10. `followup_affordances`: customer detail, aging explanation, credit utilization explanation, source-period/as-of explanation

The implementation should reuse the existing composite runtime contracts wherever possible.

It should not create a customer-risk-specific service-level branch.

## 9. Implementation Order

### 3.4A: Design Lock

Status: complete with this document.

Deliverables:

1. approved business meaning
2. approved component metrics
3. blocked concepts
4. compatibility policy
5. next contract targe

### 3.4B: Composite Registry Contrac

Status: complete for the current delivery slice.

Deliverables:

1. metadata entry for `customer_risk_as_of`
2. family variation policy
3. primary/supporting metric declaration
4. blocked variation declaration
5. row degradation policy

Implementation note:

1. the earlier draft `customer_credit_overdue_composite` contract was not duplicated
2. it was aligned into the approved `customer_risk_as_of` vocabulary
3. the family is active as a governed customer-risk concep
4. the concrete default artifact remains `blocked_missing_data`
5. the assembly remains `blocked_missing_data`
6. this is intentional because the required primary overdue-amount ranking execution is not yet governed
7. focused registry and state tests assert this fail-closed behavior

### 3.4C: Risk Artifact Assembly

Status: complete for the current delivery slice.

Deliverables:

1. reusable assembly path for customer as-of risk rows
2. same-as-of validation
3. row provenance
4. missing-component evidence

Implementation note:

1. `customer_overdue_amount_as_of_date` is now a governed business definition
2. `customer_overdue_amount_as_of_date_formula` is now an active governed formula
3. `customer_overdue_amount_as_of_scalar_execution` and `customer_overdue_amount_as_of_ranking_execution` are active governed KPI executions
4. the customer risk artifact now references an existing primary overdue-amount ranking execution
5. `customer_risk_as_of_default_composite` is active at the metadata/contract level
6. `customer_as_of_risk_ranking_assembly` is active at the metadata/contract level
7. runtime support for scalar overdue amount and top customers by overdue amount is covered by focused tests
8. this does not yet mean broad user-facing `show risky customers` behavior is fully released

The user-facing ranking and filter release policy remains in `3.4D`.

### 3.4D: Ranking And Filtering

Status: complete for the current delivery slice.

Deliverables:

1. default ranking by overdue amoun
2. approved credit-utilization variation if metadata supports i
3. threshold filtering where active
4. blocked-safe behavior for unapproved severity labels

Implementation note:

1. broad customer-risk requests are now resolved by family metadata, not by a one-off prompt branch
2. `customer_risk_as_of` declares approved default trigger aliases, default primary metric, default supporting metrics, and default as-of-date policy
3. the composite runtime now supports metadata-driven default primary metric resolution for families that explicitly declare default triggers
4. commercial ranking families remain protected from risk-family activation by family-owned subject and basis matching
5. as-of-date composite execution now passes the resolved as-of date into component KPI executions
6. `outstanding_amount` is derived through artifact metadata from the primary overdue-amount row when no separate component execution is approved
7. the risk artifact now references ranking executions only; scalar-only component leakage was removed
8. rendering now shows approved default supporting metrics in composite tables
9. KPI execution is lazy-loaded by the composite runtime so import-time customer/Frappe helpers do not leak across test modules
10. focused verification passed across composite runtime, composite registry/state, and KPI runtime tests

The slice intentionally does not add collection recommendations, predictive risk labels, or hidden weighted risk scores.

### 3.4E: Detail And Follow-Up Suppor

Status: complete for the current delivery slice.

Deliverables:

1. row-to-customer detail continuation
2. aging and utilization explanation follow-ups
3. context switching without stale artifact inheritance
4. business-natural fallback for unsupported follow-ups

Implementation note:

1. the customer-risk composite now emits a normalized follow-up artifact using its declared `local_followup_family_id`
2. `customer_risk_as_of` keeps `customer_entity_detail` as the follow-up family instead of being forced into `ranking_analytics`
3. ranked risk rows now carry customer identity, rank, primary/supporting risk metrics, source composite family, and as-of date
4. grounded turn context now exposes known customer entities from the risk table, including row rank and source family
5. approved follow-up affordances from metadata are carried forward for aging breakdown, credit utilization explanation, customer detail, and as-of-date explanation
6. the helper remains backward compatible with older/simple family-resolution test contracts
7. focused tests verify that risk results now expose customer detail follow-up context without weakening commercial ranking behavior
8. composite artifacts that declare a local detail follow-up family are now recognized by the shared follow-up boundary through metadata, not by a `customer_risk_as_of` or `customer_entity_detail` special case
9. the same metadata-derived helper now controls grounded follow-up support, entity-detail context domain expansion, entity navigation breakout checks, and item-stock follow-up eligibility
10. focused follow-up interpreter tests verify that risk customer follow-ups stay grounded while unrelated entity-navigation asks can still break out safely
11. the composite runtime test fixture is now order-independent for local/container unittest runs
12. ranked-row entity follow-up routing now supports generic ordinal references such as `first`, `second`, `rank 1`, `row 2`, and `No. 3`
13. ordinal routing is shared across ranked customer, supplier, item, and future entity artifacts because it uses grounded `known_entities` plus rank/position metadata
14. ambiguous multi-row deictic requests such as `tell me more about that customer` remain guarded instead of silently choosing the first row
15. the service facade only received minimal orchestration glue to pass the raw user message into the shared runtime-message compilation helper
16. composite ranked-row metric explanations are now handled by a shared `composite_evidence_support` helper, not by a customer-risk-specific service branch
17. selected-row questions such as `why is the first customer risky` and `explain rank 2` can be answered from current governed composite evidence when a row is safely selected
18. the answer explicitly states that it is evidence from the current governed artifact and not a prediction, severity label, or collection recommendation
19. the artifact boundary lane now sees composite ranked-row evidence through the existing direct-evidence seam
20. ambiguous multi-row explanation follow-ups now return a business-natural row/customer choice prompt through the shared composite evidence boundary, instead of falling through to runtime guessing or a generic unsupported response
21. this fallback is composite-generic: it uses source composite metadata, ranked-row identity, and subject alias wording rather than a customer-risk-specific branch
22. `show customer risk` now resolves through the governed `customer_risk_as_of` composite instead of falling back to the older Accounts Receivable Aging artifac
23. the missing family-metric bridge on customer-risk ranking KPI executions was fixed in metadata so component artifacts expose `overdue_amount`, `overdue_ratio`, and `credit_utilization` consistently
24. current-artifact evidence preservation now accepts any proven governed artifact evidence answer, not only older entity-detail evidence contracts, while still respecting clarification-required contracts
25. this prevents evidence-capable composite follow-ups from breaking out to fresh AR Aging queries
26. ambiguous row-choice prompts now flow through the grounded evidence answer lane rather than recovery guidance, so they do not poison the next selected-row follow-up
27. selected-row explanations support ordinal, rank, and named-row references such as `why is the first customer risky`, `explain rank 2`, and `why is Ko Nay Lin Mobile Center risky`
28. composite percentage formatting now normalizes decimal ratios into percent display, so values such as `0.6203` render as `62.03%`
29. row-choice presentation now uses markdown bullet rows for cleaner browser rendering
30. focused and broad regression coverage verifies composite routing, row selection, ambiguous deictic clarification, named-row explanation, context-switch safety, recommendation non-capture, metadata execution shape, and adjacent follow-up behavior

Remaining work:

1. route deeper aging-breakdown requests to governed customer detail/KPI evidence when bucket-level evidence is not present in the current composite artifac
2. add a broader stale-context UAT pack across risk, product, supplier, customer, and financial-statement contexts
3. define the Phase `3.5` governed reasoning boundary for explanation, recommendation, and driver-analysis style questions

### 3.4F: UAT And Guardrails

Status: next.

Deliverables:

1. browser/UAT question pack
2. regression coverage for broad phrasings
3. proof that new phrasings do not require new branches
4. closure notes for Phase `3.5`

## 10. Test And UAT Seeds

Future slices should cover these user-facing examples:

1. `show risky customers`
2. `show overdue customers with credit utilization`
3. `show top overdue customers as of today`
4. `show customers above credit limit`
5. `why is this customer risky?`
6. `show me the aging breakdown for that customer`
7. `show the customer details for the first one`
8. `which customers need credit review?`

Expected behavior:

1. supported views produce governed composite evidence
2. unsupported recommendation asks fail closed naturally
3. predictive or advisory asks do not fabricate advice
4. follow-ups remain bound to the selected customer row or clarify when the row is ambiguous

## 11. Definition Of Done For 3.4A

`3.4A` is complete when:

1. customer-risk-as-of meaning is locked
2. approved and blocked concepts are explici
3. metric/component policy is tied to existing governed metadata
4. runtime work is intentionally deferred to `3.4B`
5. no new one-off code path has been introduced

This slice is intentionally documentation and design only.

That is the safer enterprise move before activating a risk-related runtime surface.
