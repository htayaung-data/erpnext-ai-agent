# Sales Console Mini-Phase 5 Shared Report Archetype

Status: active report-runtime foundation
Date: 2026-04-18
Last updated: 2026-05-03
Source of truth: Mini-Phase 5 report classification, existing list runtime, frozen Sales Console visual system

## 1. Purpose

This note defines the shared report-page standard for the remaining Sales Console report destinations.

It exists so that:

1. reports are built as one product family
2. filters, summaries, and tables behave consistently
3. each new report page becomes a data variant, not a new page invention
4. Mini-Phase 5 stays enterprise grade instead of becoming seven unrelated report screens

## 2. Core Architecture Decision

The correct implementation is:

1. keep document pages on the child-page runtime
2. keep queues and review pages on the list runtime
3. introduce a dedicated shared report runtime for report-family destinations
4. keep all three inside one visual language and spacing system

This means reports should not be implemented by stretching the worklist shell until it becomes ambiguous.

Reports need their own runtime because they answer a different user question.

Worklists answer:

1. what needs action now

Reports answer:

1. what is true
2. what pattern is emerging
3. what needs management or commercial review

## 3. Shared Report Page Structure

Every report page should follow the same six-layer structure.

### 3.1 Report header

Purpose:

1. define the report title
2. explain the report’s decision purpose in one sentence
3. establish visible scope

Required content:

1. kicker
2. title
3. subtitle
4. scope line

Rule:

1. no decorative hero treatment
2. no oversized metrics in the header itself

### 3.2 Filter band

Purpose:

1. make active report filters explicit
2. support quick review without opening native report builders

Required content:

1. primary filter controls
2. active filter chips or summary
3. reset / refresh / export actions when relevant

Rule:

1. filters must stay minimal
2. do not expose every native report option if it reduces trust or clarity

### 3.3 KPI summary row

Purpose:

1. answer the first business question in seconds
2. orient the user before they scan the full table

Typical KPI types:

1. total value
2. visible rows
3. conversion rate
4. lost count
5. overdue exposure
6. settlement coverage

Rule:

1. only show KPIs that matter to that report
2. no generic placeholder metrics

### 3.4 Results surface

Purpose:

1. present the trusted report table
2. keep rows readable and export-friendly
3. allow direct navigation to underlying records where valid

Required content:

1. results title
2. row count / scope meta
3. primary report table

Rule:

1. the table is the primary product surface
2. no decorative chart before the table
3. navigation should exist only when it helps action or review

### 3.5 Optional secondary surface

Purpose:

1. support a second view only when the report genuinely needs it

Examples:

1. a compact trend strip
2. a grouped summary table
3. exception breakout

Rule:

1. optional means optional
2. do not add a second surface just to look “complete”

### 3.6 State surface

Required states:

1. loading
2. empty
3. restricted
4. error

Rule:

1. state surfaces must explain why the table is missing
2. empty does not equal broken
3. restricted does not equal error

## 4. Backend Contract

The report runtime should consume one normalized payload contract.

Recommended structure:

1. `page`
2. `summary`
3. `filters`
4. `metrics`
5. `results`
6. `secondary`
7. `action_targets`

### 4.1 Page block

Contains:

1. route key
2. title
3. optional report family label

### 4.2 Summary block

Contains:

1. kicker
2. title
3. subtitle
4. scope facts

### 4.3 Filters block

Contains:

1. normalized controls the runtime can render
2. active filter chips
3. export / refresh actions

### 4.4 Metrics block

Contains:

1. ordered KPI cards
2. per-card tone
3. per-card label, value, meta

### 4.5 Results block

Contains:

1. title
2. note
3. columns
4. rows
5. row actions
6. state when no table is available

### 4.6 Secondary block

Contains:

1. optional grouped view or trend view
2. same normalized structure rules

### 4.7 Action targets

Contains:

1. record navigation targets
2. export target if exposed
3. fallback native target when the productized report cannot render

## 5. Frontend Runtime Responsibilities

The shared report runtime should:

1. render the report shell
2. render normalized filters
3. render KPI cards
4. render primary results table
5. render optional secondary surface
6. render state surfaces
7. route row-level record opens safely

It should not:

1. contain report-specific business calculations
2. infer ERP meaning from display labels
3. hardcode per-report layouts in the renderer

## 6. Report Variants

The shared shell should support four report variants.

### 6.1 Performance summary variant

Use for:

1. `Sales Analytics`

Emphasis:

1. KPI row first
2. summary table second

### 6.2 Execution review variant

Use for:

1. `Sales Order Analysis`
2. `Collections Status`

Emphasis:

1. dense operational table
2. review-first metrics

### 6.3 Trend variant

Use for:

1. `Trend Analysis`

Emphasis:

1. compact directional summary
2. trend-supporting table
3. selectable document type for `Sales Invoice`, `Sales Order`, and `Quotation`

### 6.4 Exception / history variant

Use for:

1. `Lost Quotations`
2. `Item-wise Sales History`

Emphasis:

1. stronger filters
2. table-first review
3. clear exception or history framing

## 7. Design Rules

To stay enterprise grade, every report page must follow these rules:

1. charts are deferred unless they are clearly more useful than the table
2. filters must be comprehensible without training
3. colors indicate meaning, not decoration
4. header text must stay brief
5. rows must support real follow-up, not just reading
6. typography must remain aligned with Sales Console and worklists
7. summary cards must stay quieter than the document pages

## 8. Immediate Build Sequence

After this archetype note, the correct next implementation order is:

1. create the shared report registry in backend
2. create the shared report page runtime
3. implement first report cluster:
   1. `Sales Analytics`
   2. `Sales Order Analysis`
   3. `Trend Analysis`

Current report-family correction:

1. `Collections Status` is the accepted settlement/receivables report direction.
2. `Payment Terms Status for Sales Order` is not the current Sales Console report target.
3. `Sales Order Trends` is not part of the current role-based report-card catalog.
4. `Trend Analysis` replaces visible `Quotation Trends`; the legacy route remains only as a compatibility alias.
5. A standalone dashboard page is not part of the final report family.
6. validate latency, empty states, and route integrity before adding any future report cluster
