# First Approved Expansion Candidate

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: second approved behavioral-class expansion candidate after the frozen Phase 3 baseline  
Status: approved for design and controlled implementation review

## Candidate Name
`contribution_share`

## Simple Description
This class answers business questions of the form:

1. show how much each entity contributes to the total
2. show the percent share of total revenue, sales, or purchase amount
3. rank entities while keeping their share of total visible

In simple business language, this is the class for:

- `who contributes how much to the whole`
- `what percent of the total comes from each customer, supplier, or item`

## Why This Is The Right Next Candidate
This is the next safe expansion target because it stays inside deterministic ERP read behavior while adding high business value for current January 2026-heavy data.

It is safer than jumping into:

1. causal diagnosis
2. recommendation generation
3. scenario estimation
4. soft conversational re-evaluation behavior

It also fits the current dataset better than time-comparison-heavy classes.

## Business Value
This class supports practical management questions such as:

1. `Top 10 customers contribution share of total revenue last month`
2. `Show suppliers contribution share of total purchase amount last month`
3. `Show items share of total sales last month`

This is valuable because it helps users move from raw ranking into simple percentage context without moving into advisory behavior.

## Why It Fits The Current Architecture
This class can reuse current strong foundations:

1. deterministic report selection
2. governed ontology normalization
3. governed capability metadata
4. stable transform/projection follow-up behavior
5. replay and browser/manual evidence discipline

The new logic should focus on:

1. contribution-language normalization
2. contribution-capable report selection
3. deterministic percent-of-total calculation on bounded result sets

## Non-Goals
This class is not:

1. concentration-risk analysis
2. Pareto / cumulative share analysis
3. consultant-style narrative interpretation
4. causal explanation
5. recommendation generation
6. time-comparison share analysis
7. multi-group share tables such as territory plus salesperson in the same first slice

## Initial Scope
Initial supported domains:

1. sales
2. purchasing

Initial supported entity grains:

1. customer
2. supplier
3. item

Initial supported metric families:

1. revenue
2. purchase amount

Approved first-slice report families:

1. `Customer Ledger Summary`
2. `Supplier Ledger Summary`
3. `Item-wise Sales Register`

Explicitly deferred from the first slice:

1. territory share
2. item-group share
3. supplier-group share
4. customer-group share
5. cumulative share / running total share

## Example User Questions
Examples for design coverage:

1. `Top 10 customers contribution share of total revenue last month`
2. `Show customers share of total revenue last month`
3. `Top 10 suppliers share of total purchase amount last month`
4. `Show items contribution share of total sales last month`

These are examples only. The class must generalize by contract, not by memorizing prompts.

## Proposed Class Contract

### Input Shape
Expected normalized inputs:

1. entity grain
2. base metric
3. optional ranking limit
4. optional time scope
5. optional entity filter such as company
6. contribution-share intent

### Output Modes
Allowed output modes:

1. detail list with:
   - entity grain
   - base amount
   - contribution share
2. top-n list when explicitly requested
3. restrictive projection follow-up on the returned result
4. scale follow-up where the base metric is scaled and contribution share remains stable

Not allowed:

1. causal explanation
2. recommendation output
3. cumulative distribution analysis
4. variance or diagnostic reasoning

### Clarification Rules
Clarify when one of these is missing and required:

1. the business metric is missing
2. the grouping entity grain is missing
3. the ask requests a deferred grouping not approved for the first slice

Do not clarify when:

1. the grain and metric are explicit
2. the request maps deterministically to one approved first-slice report family

### Follow-Up Rules
Allowed follow-ups:

1. `Show only customer, revenue and contribution share`
2. `Top 5 only`
3. `Show in Million`

Follow-up behavior must reuse the active result contract and obey existing transform/projection rules.

## Required Governed Inputs Before Runtime Work

### Ontology Additions
Need governed support for:

1. contribution language
2. share-of-total language
3. percent / percentage wording

These must remain ontology-driven, not runtime keyword hacks.

### Capability Metadata Additions
Important reports/capabilities must declare:

1. contribution-capable metrics
2. primary dimension alignment
3. aggregate-row policy where relevant
4. safe contribution output columns

### Runtime Expectations
Runtime may:

1. normalize contribution-share language
2. bind the request to governed contribution-capable reports
3. compute contribution share deterministically from the returned row set
4. preserve active-result follow-up behavior

Runtime may not:

1. hardcode prompt-to-report maps
2. special-case one business sentence because one UAT prompt failed
3. silently widen the class into concentration-risk or recommendation behavior

## Risk Tier
Default tier: `Tier 2`

Rule:

- finance-adjacent customer and supplier contribution flows must be validated with Tier 1 rigor even though the class baseline remains Tier 2

## Required Validation Before Runtime Implementation
No implementation is approved until these assets exist:

1. class definition document
2. ontology additions plan
3. capability metadata additions plan
4. replay suite design
5. variation matrix
6. curated browser/manual golden pack
7. targeted unit/module regressions
8. impacted-suite rerun plan

## Required Existing-Suite Reruns Once Implementation Starts
Because this class touches shared read behavior, the minimum reruns after implementation must include:

1. affected new class suite in full
2. `core_read`
3. `multiturn_context` if follow-up behavior is touched
4. `transform_followup` if result reuse behavior changes
5. standing browser smoke pack

## Approval Decision
This candidate is approved for:

1. design-preparation completion
2. formal implementation-readiness review
3. controlled first-slice runtime implementation after approval conditions are recorded
