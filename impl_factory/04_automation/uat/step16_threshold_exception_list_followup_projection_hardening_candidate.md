## Threshold Exception List Follow-Up Projection Hardening Candidate

Date: 2026-03-04  
Owner: AI Runtime Engineering  
Scope: proposed next bounded hardening slice for `threshold_exception_list`

### Candidate Name
- `threshold_exception_list_followup_projection_hardening`

### Purpose
This slice exists to broaden the already-valid core threshold class in a controlled way.

It is not a new base behavior class.  
It is a hardening slice for advanced same-session threshold result usage.

### Why This Exists
Current status:

1. core threshold slice is green in replay
2. core threshold browser behaviors are materially working
3. some richer projection/display variants are still uneven

That means the next work should be:

1. bounded
2. variation-driven
3. class-level
4. not open-ended prompt polishing

### Approved Hardening Scope
This hardening slice may include:

1. threshold result projections such as:
   - `Item Code, Item Name and Stock Qty`
   - `Invoice, Customer Name and Invoice Amount`
2. label normalization for threshold result columns where:
   - business dimension labels should stay specific
   - duplicate business metric meaning should not appear
3. same-session follow-up projection consistency after:
   - threshold value correction
   - scale-only follow-up
   - top-n follow-up

### Out Of Scope
Still do not include:

1. causal explanations
2. business advice
3. recommendation generation
4. complaint-style re-evaluation prompts as advisory behavior
5. compound multi-threshold logic expansion beyond the existing unsupported envelope

### Required Assets Before Runtime Work
Before implementation begins for this hardening slice, prepare:

1. follow-up projection variation matrix for threshold results
2. replay add-on cases covering:
   - stock threshold projection variants
   - invoice threshold projection variants
3. small browser/manual add-on pack for the same variants
4. rerun impact note for:
   - `threshold_exception_list`
   - `transform_followup`
   - standing browser smoke pack if shaping/state changes are shared

### Boundary Rules
Must not do:

1. prompt-to-report maps
2. case-ID logic
3. hidden phrase routing
4. informal widening of supported scope without updating assets

Must do:

1. use governed metadata and ontology
2. fix projection/display behavior at class level
3. keep replay and browser evidence aligned

### Approval Recommendation
- Not for immediate implementation by default
- Ready for asset preparation and formal approval review if/when this broader variation support becomes a business priority

