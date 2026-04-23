# Qwen ERP Governed Scope Coverage Phase 0 Baseline

Status: active baseline note  
Date: 2026-04-12  
Scope: Phase 0 baseline for governed scope coverage research before Round 1 analysis

## 1. Purpose

This note establishes the baseline rules for governed scope coverage research.

It exists so the next research and implementation slices do not drift into:

1. prompt-by-prompt debugging
2. single-case rescue logic
3. guessing support from isolated browser results
4. treating `ERP has data` as `assistant has governed support`

Phase 0 is done once.

After Phase 0 is stable, later research should run in rounds.
Each round should apply the same Phase 1 to Phase 5 method to a bounded scope set.

## 2. Authoritative Sources

The following documents are the current authority for this baseline.

### 2.1 Enterprise Development Rules

1. `impl_factory/00_governance/current_docs/qwen_erp_enterprise_development_guidelines_2026-04-04.md`

Key governing rules from that note:

1. contract first
2. metadata owns business policy
3. runtime consumes typed contracts and fails closed
4. no keyword routing
5. no hardcoded single-case fixes
6. no hidden fallback
7. no raw-message business branching after structured interpretation already exists

### 2.2 Delivery Roadmap

1. `impl_factory/00_governance/current_docs/qwen_erp_phase_implementation_roadmap_2026-04-04.md`

Key roadmap rule for this research:

1. implement one bounded slice at a time
2. phase work must stay debt-aware but product-led
3. phase progress must not be derailed by speculative cleanup

### 2.3 Active Phase 3 Design Ownership

1. `impl_factory/00_governance/current_docs/qwen_erp_phase3_composite_governed_artifact_design_2026-04-10.md`
2. `impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_phase3_3_ranking_projection_and_evidence_contract_design_2026-04-11.md`
3. `impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_phase3_3b_3c_entity_lookup_and_evidence_seam_design_2026-04-12.md`

Current ownership conclusion:

1. the project is in Phase `3`
2. the currently active bounded implementation seam is Phase `3.3`
3. the immediate implementation work sits inside `3.3B` and `3.3C`
4. governed scope expansion beyond the current seam must not be mixed into current runtime edits without research evidence

### 2.4 Current System Evaluation

1. `impl_factory/00_governance/current_docs/phase3_entity_lookup_scope/qwen_erp_ai_assistant_enterprise_evaluation_2026-04-12.md`

Key conclusion from that evaluation:

1. the system already has real enterprise architecture
2. the current issue is uneven seam maturity, not lack of foundation
3. the correct next move is bounded seam completion, not reinvention

## 3. Current Phase Placement

This research does not replace the current roadmap.

It supports the roadmap by reducing guesswork before wider governed scope activation.

Current placement:

1. active implementation track remains Phase `3.3`
2. current runtime work remains ranking projection and entity lookup / evidence seam cleanup
3. governed scope coverage research is a supporting governance activity
4. it should inform later scope expansion, not interrupt Phase `3.3` unless it proves a real blocker

Practical decision:

1. finish the current bounded `3.3` work on the current approved governed scope
2. use this research program to prepare safe expansion after that

## 4. What Phase 0 Must Define

Phase 0 must define five things clearly before deeper analysis begins.

### 4.1 Definitions

Use these terms exactly during later research.

`declared`

1. present in metadata or contract definitions
2. not yet proven to execute

`active`

1. connected through the real runtime path
2. reachable without one-off debug code

`verified`

1. proven by code-level evidence and bounded execution checks
2. not assumed from metadata alone

`generalized`

1. implemented in a shared seam
2. not customer-only, supplier-only, item-only, or phrase-only unless the phase explicitly scopes it that way
3. future reuse is controlled by metadata/contract activation rather than copied Python branching

`governed support`

1. a request can be interpreted into typed state
2. routed through approved metadata/capability/family seams
3. executed against approved ERP authority
4. rendered without rediscovering business meaning from raw text
5. followed up safely or failed closed explicitly

### 4.2 Evidence Standard

No support claim is valid unless it is backed by at least these evidence layers:

1. metadata evidence
2. runtime seam evidence
3. bounded execution evidence

Browser/UAT evidence is useful, but it comes after those three.

### 4.3 Stop Rules

Later research phases must stop when:

1. the bounded round scope has been mapped sufficiently for design
2. evidence is enough to classify a gap as:
   - missing metadata
   - missing runtime consumption
   - missing governed source
   - missing renderer/follow-up support
3. extra digging would not change the implementation decision

Later research phases must not stop because:

1. one prompt worked once
2. one prompt failed once
3. a theoretically wider cleanup looks attractive

### 4.4 Scope Granularity

The research unit is not "the whole ERP."

The research unit is one bounded scope round.

Each round should contain a small set of closely related grains or domains.

### 4.5 Round Method

Phase 0 happens once.

After that, each round should run:

1. Phase 1: front-door and metadata inventory
2. Phase 2: contract and runtime seam mapping
3. Phase 3: behavior truthing
4. Phase 4: gap classification and priority
5. Phase 5: bounded design for implementation

This means the process is:

1. one Phase 0
2. then repeated Phase 1 to Phase 5 per round

## 5. Research Taxonomy

Later rounds should classify scope using the same taxonomy.

### 5.1 Entity Navigation

1. customer
2. supplier
3. item or product
4. warehouse
5. sales person
6. territory

### 5.2 Document Navigation

1. sales invoice
2. purchase invoice
3. sales order
4. purchase order
5. delivery note
6. payment entry

### 5.3 Analytical Scopes

1. ranking
2. trend
3. KPI
4. composite
5. aging
6. inventory

### 5.4 Evidence And Detail Scopes

1. profile
2. lifecycle
3. credit or payable status
4. overdue
5. first activity
6. policy sections

### 5.5 Continuation Scopes

1. deictic follow-up
2. projection change
3. time correction
4. subject switch
5. fresh breakout

## 6. Round Structure

The research should not attempt the full ERP universe in one pass.

Recommended early rounds:

### 6.1 Round 1

1. customer
2. supplier
3. item or product

Reason:

1. these are high-frequency business nouns
2. they are already partially represented across the system
3. recent live failures show seam unevenness here
4. they are the best place to prove the research method

### 6.2 Round 2

1. sales invoice
2. sales order
3. purchase invoice
4. purchase order
5. delivery note

### 6.3 Round 3

1. receivable
2. payable
3. inventory
4. warehouse
5. stock movement or related inventory evidence seams

Further rounds may be added later, but only after the first rounds prove useful.

## 7. Phase 0 Practical Outputs

Phase 0 is complete only when the following are true:

1. the authority docs are identified
2. the current roadmap placement is explicit
3. the definitions for declared, active, verified, and generalized are fixed
4. the evidence standard is fixed
5. the round structure is fixed
6. Round 1 is chosen

## 8. Round 1 Starting Decision

Round 1 should now begin with:

1. customer
2. supplier
3. item or product

Round 1 objective:

1. map where those grains already exist in metadata
2. map where those grains already execute in runtime
3. map where support is uneven across navigation, detail, analytics, and follow-up seams
4. separate true missing scope from missing activation and missing handoff

## 9. What This Baseline Explicitly Avoids

This baseline does not authorize:

1. immediate runtime widening
2. broad refactor
3. grain-specific rescue logic
4. phrase whitelists
5. support claims based only on ERP data existence

This baseline does authorize:

1. disciplined coverage mapping
2. bounded round-based analysis
3. evidence-backed priority decisions
4. later design notes that reuse the existing contract and metadata ecosystem

## 10. Phase 0 Status

Phase `0` is established by this note.

Next step:

1. start Round `1`, Phase `1`
2. inventory front-door and metadata coverage for:
   - customer
   - supplier
   - item or product
