# Behavioral Class Development Contract

Date: 2026-03-02  
Owner: AI Runtime Engineering  
Scope: enterprise-safe development, expansion, and release of new behavioral classes after Phase 2 stabilization  
Status: draft governing contract for the next expansion track

## Purpose
This contract defines how the product may safely expand beyond the currently stabilized behavior set.

It exists to stop five failure modes:

1. adding new business questions without a class design
2. growing runtime keyword logic to make specific prompts work
3. breaking existing classes while expanding new ones
4. shipping new capabilities without replay/manual evidence
5. confusing language normalization with business execution rules

This contract is for engineering delivery and quality governance. It is not a runtime JSON schema.

## Core Principle
The system must expand by **behavioral class**, not by isolated prompt.

A new capability is not considered delivered because:

1. one prompt worked
2. one browser path looked correct
3. one replay case passed

A new capability is considered delivered only when:

1. the behavior class is explicitly defined
2. the class contract is explicit
3. the required metadata/ontology support exists
4. regression assets exist
5. risk-appropriate validation is green

## Non-Negotiable Boundaries
1. No prompt-to-report maps in runtime code.
2. No case-ID hacks.
3. No “if message contains X then do Y” business routing in runtime modules.
4. No hidden business fallback maps inside:
   - `read_engine.py`
   - `memory.py`
   - `semantic_resolver.py`
   - `response_shaper.py`
   - `quality_gate.py`
   - `spec_pipeline.py`
5. No silent behavior override that cannot be explained by contract, ontology, metadata, or persisted state.
6. No new class goes live without both replay evidence and manual golden evidence appropriate to its risk.

## What A Behavioral Class Is
A behavioral class is a reusable execution family, not a topic list.

Examples:

1. ranking top/bottom
2. restrictive detail projection
3. transform last result
4. correction/rebind
5. latest-record listing
6. KPI aggregate
7. trend time series
8. comparison

A behavioral class may apply across many domains:

1. sales
2. purchasing
3. finance
4. inventory
5. HR
6. operations

## Required Inputs Before Implementing A New Class
Before code changes begin, the following must be written down:

1. business objective
2. behavior class name
3. risk tier
4. supported domains
5. expected input shape
6. expected output modes
7. clarification rules
8. correction/rebind rules
9. transform/follow-up rules
10. safety and non-goals

If these are not defined, the class is not ready to build.

## Required Assets For Every New Class
Every behavioral class must have all of the following:

1. class definition document
2. governed ontology additions, if needed
3. governed capability metadata additions, if needed
4. replay manifest cases
5. browser/manual golden cases
6. variation matrix for phrasing and follow-up variants
7. targeted unit or module-level regressions
8. impact-based existing-suite rerun plan

## Design Rules For Class Development

### 1. Language Understanding Lives In Ontology
Use ontology for:

1. synonyms
2. abbreviations
3. jargon
4. normalized metric/dimension/action semantics
5. transform ambiguity semantics

Do not use ontology as a hidden routing table.

### 2. Execution Truth Lives In Metadata
Use capability/report metadata for:

1. primary grain
2. supported dimensions
3. supported metrics
4. summary vs detail
5. ranking support
6. aggregate-row policy
7. transform-safe columns
8. domain ownership

Do not force runtime to guess this if metadata can declare it explicitly.

### 3. Runtime Must Stay Generic
Runtime code may:

1. normalize to canonical concepts
2. match canonical intent to metadata
3. preserve active result contracts
4. enforce deterministic precedence
5. validate quality and safety

Runtime code may not:

1. special-case a business prompt
2. special-case a report because one UAT prompt failed
3. grow uncontrolled lexical behavior outside governed data

## Required Validation For A New Class

### A. New-Class Validation
Every new class needs:

1. full replay suite for the class
2. class variation matrix coverage
3. browser/manual golden coverage
4. targeted unit/regression tests

### B. Existing-Class Regression Validation
Do not rerun everything by default, but do not rerun only the new class either.

For each new class, engineering must define impacted shared surfaces:

1. resolver
2. memory/state
3. transform-followup
4. shaping
5. quality gate
6. latest-record flow
7. write safety if touched

Then rerun:

1. the new class suite in full
2. the affected existing suites
3. the core smoke pack

### C. Milestone/Release Validation
At milestone or release time:

1. rerun broader replay coverage
2. rerun the release gate
3. refresh manual golden evidence

## Variation Matrix Rule
No class is accepted from one or two prompts.

Each class must define a variation matrix across:

1. base ask
2. equivalent phrasing
3. projection variant
4. restrictive `only` variant
5. correction variant
6. transform variant
7. topic-switch variant, if applicable
8. domain/grain variants, if applicable

The matrix is the unit of closure, not the anecdotal prompt.

## Risk Tiering
Each class must be assigned a risk tier:

### Tier 1
High business or safety impact.
Examples:

1. write behavior
2. finance-critical reads
3. receivables/payables decisions
4. destructive operations

Required:

1. deep replay
2. manual golden
3. explicit owner
4. release-gate evidence

### Tier 2
Important analytical behavior with lower safety risk.
Examples:

1. rankings
2. projections
3. time series
4. comparisons

Required:

1. replay
2. variation matrix
3. targeted browser smoke

### Tier 3
Low-risk convenience behavior.
Examples:

1. formatting-only transformations
2. display-only refinements

Required:

1. focused regression
2. smoke coverage if shared surfaces are touched

## Release Rules For New Classes
A new behavioral class is eligible for release only when:

1. class definition exists
2. ontology/metadata assets are committed
3. replay evidence is green
4. manual golden evidence is green
5. impacted legacy suites are green
6. risk-tier obligations are satisfied
7. no known retry-to-succeed behavior remains

## Disallowed Expansion Patterns
1. add more business prompts first and “formalize later”
2. fix a browser prompt without a class invariant
3. add runtime synonyms in code to make one prompt pass
4. add new classes before current shared regressions are closed
5. declare generalization from one working entity/domain pair

## Recommended Delivery Workflow
For every new behavioral class:

1. write the class definition
2. define the variation matrix
3. identify metadata and ontology needs
4. implement the smallest correct class-level invariant
5. add targeted regressions
6. run the class replay suite
7. run impacted existing suites
8. run browser/manual golden pack
9. attach evidence
10. only then mark class complete

## Current Immediate Use Of This Contract
This contract should become active after final administrative close of the current Phase 2 loop.

Its first use should be:

1. formalizing Phase 3 regression discipline
2. deciding when to safely expand to new business question families
3. preventing future work from drifting back into prompt-by-prompt patching

## Exit Condition For This Contract
This contract is superseded only when the project adopts a more formal enterprise delivery standard that includes:

1. explicit risk-tier governance
2. incident-to-regression automation
3. operational owner/SLA assignment
4. release impact matrix enforcement
