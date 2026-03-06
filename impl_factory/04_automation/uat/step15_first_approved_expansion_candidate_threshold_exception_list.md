# First Approved Expansion Candidate

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: first approved behavioral-class expansion candidate after Phase 2 closure and Phase 3 governance kickoff  
Status: approved for design and asset preparation, not yet approved for runtime implementation

## Candidate Name
`threshold_exception_list`

## Simple Description
This class answers business questions of the form:

1. show records above a threshold
2. show records below a threshold
3. show overdue / under-stock / high-outstanding exceptions
4. list the items, customers, suppliers, invoices, or warehouses that cross a business threshold

In simple business language, this is the class for:

- “show me the exceptions”
- “show me what needs attention”

## Why This Is The First Approved Expansion Candidate
This is the right first expansion candidate because it gives clear business value without forcing the product into high-risk advisory behavior too early.

It is safer than jumping into:

1. causal “why” explanations
2. recommendation generation
3. narrative business consulting
4. agentic multi-step business planning

It stays close to the now-stabilized deterministic ERP read layer.

## Business Value
This class supports practical day-to-day management use cases such as:

1. overdue invoices above a material amount
2. customers with outstanding above a threshold
3. suppliers with payable balances above a threshold
4. items below minimum stock
5. warehouses with stock balance below or above a threshold

This is valuable because it shifts the assistant from “show me data” to “show me what is important.”

## Why It Fits The Current Architecture
This class can reuse current strong foundations:

1. deterministic read routing
2. governed capability metadata
3. ontology normalization
4. projection and transform follow-up
5. browser/manual smoke discipline

The new logic should focus on:

1. threshold parsing
2. comparator semantics (`above`, `below`, `greater than`, `less than`, `over`, `under`)
3. exception-oriented output contract

## Non-Goals
This class is not:

1. causal analysis
2. recommendation generation
3. decision advice
4. freeform consultant behavior
5. write/action automation

Those belong to later higher-layer tracks, not this expansion.

## Initial Scope
Initial supported domains:

1. finance
2. inventory

Initial supported entity grains:

1. customer
2. supplier
3. invoice
4. item
5. warehouse

Initial supported metric families:

1. outstanding amount
2. grand total / invoice amount
3. stock balance
4. quantity on hand / stock quantity

## Example User Questions
Examples for design coverage:

1. `Show customers with outstanding amount above 10,000,000`
2. `Show suppliers with outstanding amount above 20,000,000`
3. `Show overdue sales invoices above 5,000,000`
4. `Show items with stock below 20 in Main warehouse`
5. `Show warehouses with stock balance below 50,000,000`

These are examples only. The class must generalize by contract, not by memorizing prompts.

## Proposed Class Contract

### Input Shape
Expected normalized inputs:

1. subject/entity grain
2. metric
3. comparator
4. threshold value
5. optional status filter
6. optional time scope
7. optional entity filter (company, warehouse, customer group, etc.)

### Output Modes
Allowed output modes:

1. detail list
2. top-n list if explicitly requested
3. restrictive projection follow-up on the returned exception list

Not allowed:

1. advisory explanation
2. recommendation output
3. causal explanation

### Clarification Rules
Clarify only when one of these is missing and required:

1. metric is missing
2. threshold value is missing
3. comparator is missing and cannot be safely inferred
4. entity grain is ambiguous

Do not clarify when:

1. all required components are clear
2. the request can be routed deterministically to a single exception-style list

### Follow-Up Rules
Allowed follow-ups:

1. `show only customer and outstanding amount`
2. `top 5 only`
3. `show as Million`
4. `same result but only invoices`

Follow-up behavior must reuse the active result contract and obey existing transform/projection rules.

## Required Governed Inputs Before Implementation

### Ontology Additions
Need governed support for:

1. comparator semantics
2. threshold language
3. exception-oriented words like:
   - overdue
   - under
   - below
   - above
   - greater than
   - less than

These must remain ontology-driven, not runtime business keyword hacks.

### Capability Metadata Additions
Important reports/capabilities must declare:

1. threshold-filterable metrics
2. valid comparator-ready columns
3. status-filter support where relevant
4. grain and domain ownership

### Runtime Expectations
Runtime may:

1. normalize comparator and metric semantics
2. bind them to governed capability metadata
3. enforce deterministic filtering and projection

Runtime may not:

1. hardcode business prompts
2. special-case one report because a UAT question failed
3. silently switch to advisory behavior

## Risk Tier
Default tier: `Tier 2`

Rule:
- any finance-critical variant used for receivable/payable decision support must be treated as `Tier 1` validation even if the base class is `Tier 2`

## Required Validation Before Implementation
No implementation is approved until these assets exist:

1. class definition document
2. ontology additions
3. capability metadata additions
4. replay suite for the new class
5. variation matrix for comparator/threshold variants
6. curated browser/manual golden pack
7. targeted unit/module regressions
8. impacted-suite rerun plan

## Required Existing-Suite Reruns Once Implementation Starts
Because this class touches shared read behavior, the minimum reruns after implementation must include:

1. affected new class suite in full
2. `core_read`
3. `multiturn_context` if follow-up/projection is touched
4. standing browser smoke pack
5. release gate if implementation is being considered for milestone close

## Approval Decision
This candidate is approved for:

1. contract design
2. ontology planning
3. capability metadata planning
4. replay/manual asset design

This candidate is not yet approved for:

1. runtime implementation
2. release scheduling

Implementation approval should happen only after the required assets above are prepared.
