# Qwen ERP Metadata Gap Audit (2026-03-25)

Status: Mini-phase 4 evidence review  
Scope: discovery outputs vs governed metadata for the high-value governed report set

## 1. Purpose

This audit answers one practical question:

1. is the current discovery foundation already useful enough to guide enterprise runtime and contract work?
2. or do we need another extraction-heavy implementation step first?

The focus is deliberately narrow:

1. compare discovered ERP surface with governed metadata
2. separate extractable ERP facts from curated semantic assumptions
3. identify the real remaining metadata gap

## 2. Discovery Snapshot Used

Live snapshot source:

1. `/home/frappe/frappe-bench/sites/erpai_prj1/private/files/qwen_discovery/latest_discovered_erp_surface.json`
2. `/home/frappe/frappe-bench/sites/erpai_prj1/private/files/qwen_discovery/latest_discovery_evaluation_summary.md`

Live counts from the current regenerated snapshot:

1. reports: `219`
2. doctypes: `963`
3. referenced doctypes: `73`
4. governed reports: `13`
5. governed report-backed entries: `12`
6. governed direct-query entries: `1`
7. governed missing report-backed entries in ERP: `0`

Important correction:

1. `Sales Invoice List` is a governed `direct_query` surface
2. it is **not** supposed to appear as an ERP `Report` document
3. discovery alignment now tracks that separately instead of calling it a missing ERP report

## 3. Priority Governed Report Inventory

### 3.1 Sales and product reports

`Sales Analytics`

1. present in live ERP: yes
2. report type: `Script Report`
3. ERP-declared filters/columns: none
4. governed hints available: yes
5. discovery can prove:
   - report exists
   - module is `Selling`
   - ref doctype is `Sales Order`
   - governed metadata expects filters such as `tree_type`, `value_quantity`, `doc_type`, `range`
6. discovery cannot prove:
   - live report really exposes both `Sales Amount` and `Quantity` together in one stable result shape
   - selector-filter behavior beyond governed assumptions

`Item-wise Sales History`

1. present in live ERP: yes
2. report type: `Script Report`
3. ERP-declared filters/columns: none
4. governed hints available: yes
5. discovery can prove:
   - report exists
   - module is `Selling`
   - ref doctype is `Sales Order`
6. discovery cannot prove:
   - exact live output columns
   - whether `Delivered Quantity` and `Billed Amount` are exposed with a grain compatible with other governed reports

`Gross Profit`

1. present in live ERP: yes
2. report type: `Script Report`
3. ERP-declared filters/columns: none
4. governed hints available: yes
5. discovery can prove:
   - report exists
   - module is `Accounts`
   - ref doctype is `Sales Invoice`
6. discovery cannot prove:
   - whether its `Qty` and `Selling Amount` are semantically safe for continuation from sales ranking artifacts
   - whether its grouping behavior preserves the same ranking basis as `Sales Analytics`

`Sales Invoice List`

1. present in live ERP as `Report` doc: no
2. governed surface type: `direct_query`
3. current judgment:
   - expected
   - not a discovery failure
4. implication:
   - discovery must track report-backed and direct-query governed surfaces separately

### 3.2 AR / AP reports

`Accounts Receivable`

1. present in live ERP: yes
2. report type: `Script Report`
3. ERP-declared filters/columns: none
4. governed hints available: yes
5. discovery can prove:
   - report exists
   - module is `Accounts`
   - ref doctype is `Sales Invoice`
6. discovery cannot prove:
   - exact live aging bucket structure
   - exact customer/party output fields without governed assumptions

`Accounts Payable`

1. present in live ERP: yes
2. report type: `Script Report`
3. ERP-declared filters/columns: none
4. governed hints available: yes
5. same pattern as receivables

### 3.3 Financial statements

`Balance Sheet`

1. present in live ERP: yes
2. report type: `Script Report`
3. ERP-declared filters/columns: none
4. governed hints available: yes
5. discovery can prove:
   - report exists
   - module is `Accounts`
   - ref doctype is `GL Entry`
6. discovery cannot prove:
   - exact live section structure
   - exact metric labels or detail-level availability

`Profit and Loss Statement`

1. present in live ERP: yes
2. report type: `Script Report`
3. ERP-declared filters/columns: none
4. governed hints available: yes
5. same pattern as balance sheet

`Cash Flow`

1. present in live ERP: yes
2. report type: `Script Report`
3. ERP-declared filters/columns: none
4. governed hints available: yes
5. same pattern as balance sheet

## 4. Main Findings

### 4.1 Discovery is already useful

The discovery foundation is not theoretical anymore.

It already gives us:

1. live ERP report presence
2. report type breakdown
3. module and ref doctype surface
4. governed/live alignment
5. a clean separation between:
   - ERP-declared surface
   - governed-hint surface
   - direct-query governed surfaces

That is enough to support later contract families and governance work.

### 4.2 The dominant remaining gap is not missing report discovery

The real gap is:

1. most runtime-critical governed reports are `Script Report`s
2. those reports expose no useful filters or columns through the `Report` document itself
3. so generic ERP metadata extraction cannot prove enough semantic/runtime compatibility on its own

In short:

1. discovery can prove existence and rough surface
2. discovery cannot yet prove meaning-preserving compatibility

### 4.3 Curated semantics are still required

For the priority governed reports, discovery alone cannot safely decide:

1. whether two reports are grain-compatible
2. whether a column from one report can enrich another artifact
3. whether a metric union preserves business meaning
4. whether a report switch is safe continuation or a fresh query

So the enterprise boundary remains:

1. discovery tells us what exists
2. curated metadata and contracts decide what is safe to do with it

### 4.4 `Sales Analytics` is the clearest example

`Sales Analytics` is present and governed, but discovery cannot prove whether:

1. `Sales Amount`
2. `Quantity`

can be returned together from the same governed basis without changing the report mode.

That means the current enrichment weakness is fundamentally:

1. not a wording problem
2. not a report-discovery absence problem
3. a semantic compatibility problem above the discovery layer

## 5. Extractable Facts vs Curated Semantics

### 5.1 Extractable facts

These are good candidates for discovery ownership:

1. report existence
2. report type
3. module
4. ref doctype
5. ERP-declared filters
6. ERP-declared columns
7. direct-query doctype/fields for governed direct-query entries

### 5.2 Curated semantics

These should stay above discovery:

1. safe enrichment compatibility
2. safe cross-report continuation
3. grain compatibility
4. semantic equivalence between metrics
5. meaning-preserving report substitution
6. clarification-vs-rerun-vs-unavailable policy

## 6. Recommendation

### 6.1 What we should do next

Do **not** jump into another generic extraction implementation immediately.

Recommended next step:

1. treat discovery foundation as good enough for now
2. use this audit to define a curated evidence policy for runtime-relevant governed reports
3. keep the discovery/runtime boundary explicit

The next metadata-side move should be a small, explicit policy layer such as:

1. report surface evidence classes
2. what discovery proves
3. what still depends on governed semantic assumptions

### 6.2 What we should not do next

Do **not** assume that deeper generic extraction alone will solve:

1. revenue-plus-quantity enrichment
2. safe report switching
3. safe multi-metric continuation

Those are semantic compatibility problems and belong to later contract work, not this extraction chapter by itself.

## 7. Final Judgment

Mini-phase 4 discovery is in a healthy place.

Honest conclusion:

1. discovery foundation: good and useful
2. change detection: good enough
3. governed/live alignment: now more honest after separating direct-query entries
4. main remaining weakness: script-report surface is thin in ERP itself
5. next best move: governance/use of discovery, not blind extractor expansion
