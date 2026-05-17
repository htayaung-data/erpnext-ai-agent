# Qwen-Agent Consultation Brief (2026-03-22)

Scope: comprehensive context package for getting architecture guidance from Qwen on the governed ERP assistant path  
Status: active consultation brief

## Purpose

This document is intended to brief Qwen on our project so we can ask for:

1. Qwen-Agent-specific architecture advice
2. guidance on what should be governed in runtime vs left to the model
3. suggestions on follow-up handling, tool use, grounding, and latency
4. a critical review of whether we are over-constraining or under-constraining the system

This is not a request for Qwen to redesign the entire product from scratch.

We want Qwen to act as:

- a model-family specialist
- a Qwen-Agent usage reviewer
- a second opinion on architecture tradeoffs

We do **not** want blind vendor-style advice.

## Product Goal

We are building an **AI assistant inside ERPNext**.

Target product behavior:

- users ask natural business questions in ERPNext chat
- the assistant uses FAC MCP tools to query ERP data
- answers are grounded in ERP facts
- follow-up questions should feel natural and fast
- the system should eventually support:
  - read queries
  - create/update/delete actions with confirmation
  - charts/reports/dashboards in chat
  - Burmese and English
  - enterprise audit, safety, and governance

The product target is **enterprise-grade**, not a demo chatbot.

## High-Level Architecture

Current architecture path:

- ERPNext UI
- Frappe backend
- Qwen Chat page inside ERPNext
- external Qwen runtime
- Qwen-Agent
- FAC MCP
- Qwen hosted API for development
- later self-hosted Qwen via vLLM

Flow:

1. user asks in ERPNext chat
2. ERP/Frappe stores the message and session
3. ERP decides whether the request is:
   - local follow-up transform
   - sibling-switch requery
   - new query
4. for runtime-needed requests, ERP calls external Qwen runtime
5. Qwen-Agent calls FAC MCP tools
6. tool results are validated
7. grounded answer returns to ERPNext UI

## Business Constraint

Important domain fact:

- this ERP instance will hold **only one company**

That means:

- company should be treated as a governed invariant
- company should not rely on user wording
- company should not remain a recurring required filter failure path

## Why We Started This New Direction

We previously had another project path where much more orchestration and business handling was written directly in our own architecture.

That earlier work taught us important enterprise lessons:

- contracts matter
- governance matters
- validation matters
- audit matters
- model freedom alone is not enough

We started this Qwen-Agent path because we wanted:

- broader language understanding
- better messy business-language handling
- more natural follow-up behavior
- less brittle interaction than a heavily hand-built path

But we do **not** want to lose enterprise correctness.

## Enterprise Principles We Are Trying To Preserve

We are intentionally trying to build around these principles:

1. ERP/FAC remains the factual authority
2. Qwen/Qwen-Agent helps with interpretation and planning, not truth
3. contracts and validation control correctness
4. follow-ups should be typed and auditable
5. write actions must go through proposal -> preview -> confirm -> execute
6. response style must be governed
7. no architecture drift into phrase-specific hacks

## Current Contracts / Governance Layers

We already introduced these concepts:

- `InteractionContract`
- `GroundedTurnContext`
- `FollowUpResolution`
- `ExecutionPath`
- `ResponsePolicyContract`
- capability registry
- report registry
- ontology metadata
- validation metadata
- audit envelope

We also created governance/blueprint docs to avoid free-form drift.

## Current Phase Plan

Current enterprise phase plan:

### Phase 1: Contract Foundation

- `InteractionContract`
- `GroundedTurnContext`
- `FollowUpResolution`
- `ExecutionPath`

Status:

- complete

### Phase 2: Read Query Hardening

- capability registry
- report registry
- ontology and validation metadata
- tool gateway policy
- grounded validation
- audit envelope expansion

Status:

- complete

### Phase 3: Follow-Up Interpretation and Local Transform System

- semantic follow-up interpretation contract
- presentation transform path
- table presentation path
- sort/limit path
- dimension breakdown path
- column projection path
- filter refinement path
- regroup / metric-change path
- sibling-switch path
- confidence policy for semantic interpretation
- degraded-mode audit and no silent fallback

Status:

- in progress

### Phase 4: Fresh Query Compiler

- fresh-query interpretation contract
- business request to capability resolution
- governed report selection
- required filter completion
- default company/date/report-date completion
- clarify vs execute decision
- typed compiled runtime request

Status:

- not started

Later phases:

- Artifact system
- Multilingual layer
- Write safety
- Security hardening
- Enterprise UX
- Evaluation/release governance
- Productionization

## What We Have Implemented So Far

### ERP/UI Side

- separate Qwen chat page inside ERPNext
- separate session/message storage
- proper sidebar behavior
- answer rendering with tables
- message appears immediately and typing indicator behavior improved

### Runtime Side

- external Qwen runtime
- Qwen-Agent integration
- FAC MCP integration
- approved read-only tool set
- validation against approved reports and required filters
- response char limits and tool budgets

### Follow-Up Behavior

We have working examples for:

- local presentation transforms
  - `show as million`
- local sort/limit
  - `top 3`
  - `top 7`
- local dimension breakdown
  - `show by supplier`
  - `show by customer`
- sibling-switch
  - payable -> receivable

### Response Policy

We want and currently preserve this style:

1. grounded facts first
2. supporting table or numeric breakdown next
3. concise business interpretation only when relevant and grounded
4. no automatic recommendations in default factual answers
5. fuller insight/recommendations only when the user explicitly asks for analysis, comparison, recommendation, or interpretation

This is important because business users like the concise, useful interpretation layer, but we do not want every answer to become bloated or speculative.

## What Is Working Well

These are the strengths we have observed:

1. some grounded business answers are very good
2. business interpretation on payable/receivable can be genuinely useful
3. local follow-ups can be much faster than full fresh queries
4. the overall architecture is feeling closer to a real product than a raw chat UI
5. keeping grounded context for follow-ups is clearly beneficial

Examples of strong behavior:

- outstanding invoices / receivables summaries
- payable summaries
- top customers/suppliers
- concise business interpretation after grounded numbers

## What Is Not Working Reliably Yet

### 1. First-turn fresh queries are less reliable than follow-ups

Examples:

- `How much payable amount do we have as of now`
- `Analyze payable amount`

Observed failures:

- missing required report filters like `company` or `value_quantity`
- weak report selection on some revenue/sales requests

This suggests the fresh-query path is under-governed.

### 2. Some follow-ups still work only when wording is richer

Short or elliptical follow-ups can still fail or drift if they are not confidently interpreted semantically.

### 3. Some grounded answers are semantically wrong even when technically valid

Example:

- asking for all-period revenue and getting a grounded but wrong zero-heavy answer

This means current validation checks grounding, but not enough **intent-to-result consistency**.

### 4. Latency increased

We recently added:

- semantic follow-up interpretation
- confidence policy
- degraded-mode audit

This improved governance, but sometimes made runtime slower.

Observed causes include:

- extra semantic interpretation call before runtime execution
- multiple Qwen-Agent tool/LLM turns
- tool-call retries or invalid arguments

### 5. Risk of over-tightening and under-tightening at the same time

We suspect we may be:

- tightening some areas too much
- still leaving other important areas too loose

That is one of the main reasons we want Qwen’s perspective.

## Architectural Problem We Are Trying To Solve Right Now

We do **not** want to keep fixing by:

- hardcoded cases
- keyword matching
- phrase aliases
- special logic for only one business question

We want system-level fixes.

Right now, the biggest question is:

### What should be the correct division of responsibility between:

1. Qwen/Qwen-Agent semantic interpretation
2. runtime policy/gateway
3. deterministic compiler layers
4. validation and audit

## Our Current Diagnosis

Our current engineering diagnosis is:

1. follow-up interpretation is now better than before
2. fresh-query compilation is now the larger weakness
3. grounding validation is good, but semantic correctness validation is still weak
4. company should be treated as an invariant, not a repeated required filter burden
5. some agent/tool behavior may still be too free in report selection

We suspect we may need:

- a stronger `FreshQueryCompilerContract`
- better required-filter/default completion
- stronger intent-to-result validation
- better follow-up interpreter confidence policy
- clearer distinction between:
  - safe local transform
  - governed requery
  - ask for clarification

## Important Constraint For Advice

Please do **not** answer us with:

- generic LLM advice
- high-level slogans
- “fine-tune it later” without architecture detail
- “add more prompts”
- case-by-case keyword rules

We want:

- architecture-level guidance
- Qwen-Agent usage guidance
- specific tradeoff advice
- which layers should own which decisions

## Questions For Qwen

Please answer these as a critical architecture reviewer.

### A. Qwen-Agent fit

1. Is Qwen-Agent a good fit for this enterprise ERP assistant path?
2. If yes, what should Qwen-Agent own, and what should it explicitly **not** own?
3. Where should we rely on Qwen-Agent semantics, and where should we force deterministic compilation?

### B. Follow-up interpretation

4. For follow-up handling, is our current direction correct:
   - model-based semantic interpretation
   - governed validation
   - deterministic local transform or requery
5. How should we design confidence policy?
6. When semantic confidence is low, should we:
   - fallback to limited compatibility heuristics
   - ask a clarification
   - force fresh query
   - or reject?

### C. Fresh query compiler

7. Do you agree that the next major layer should be a `FreshQueryCompilerContract`?
8. How would you design a good fresh-query compiler for Qwen-Agent systems?
9. Which parts should be model-driven and which parts should be deterministic?

### D. Single-company invariant

10. Since this ERP will only ever hold one company, how should company be handled?
11. Should company be:
   - injected centrally
   - omitted from user-visible logic
   - removed from certain required-filter burdens
12. What is the safest enterprise design for this?

### E. Report selection / tool use

13. We see wrong or inconsistent report choice on some first-turn sales/revenue requests.
14. How much report selection freedom should Qwen-Agent have?
15. Should report selection be:
   - fully model-driven
   - registry-constrained
   - compiler-selected with model hints
16. What do you recommend?

### F. Validation

17. We already validate grounding and approved reports/filters.
18. What additional validation should exist to prevent semantically wrong but grounded answers?
19. How would you validate intent-to-result consistency?

### G. Latency

20. We now have stronger governance, but latency increased.
21. Where do you think the best latency savings should come from?
22. What is the right tradeoff between:
   - extra semantic interpretation call
   - agent autonomy
   - deterministic follow-up transforms
   - explicit compiler layers

### H. Response policy

23. Our preferred answer style is:
   - grounded facts first
   - supporting table next
   - concise insight only when relevant and grounded
   - deeper recommendations only on explicit request
24. Is this a good default policy for Qwen-Agent in enterprise ERP?
25. How should that policy be enforced technically?

### I. Enterprise direction

26. Based on everything above, are we over-tightening in the wrong places?
27. Are we still under-governing any critical layers?
28. If you were correcting our direction, what would you change in phase order or architecture responsibility?

## Requested Output Format From Qwen

Please answer in this structure:

1. overall assessment of our direction
2. what is correct in our current architecture
3. what is wrong or risky
4. recommended responsibility split between:
   - Qwen/Qwen-Agent
   - compiler
   - policy
   - validator
   - UI/runtime
5. recommended next implementation order
6. any Qwen-Agent-specific best practices we are missing

Please be specific and technical.

Do not give a shallow overview.

## Ready-To-Paste Prompt

Below is the condensed prompt version that can be pasted directly to Qwen:

```text
Act as a senior AI/ML architect and Qwen-Agent specialist.

We are building an enterprise AI assistant inside ERPNext.

Architecture:
- ERPNext UI
- Frappe backend
- external Qwen runtime
- Qwen-Agent
- FAC MCP
- Qwen hosted API now, self-hosted Qwen/vLLM later

Goals:
- grounded ERP answers
- natural follow-ups
- enterprise governance
- later create/update/delete with confirmation
- charts/reports/dashboards
- Burmese + English

Important business constraint:
- this ERP instance will only ever hold one company

We already implemented:
- InteractionContract
- GroundedTurnContext
- FollowUpResolution
- ExecutionPath
- capability/report/ontology/validation metadata
- tool gateway policy
- grounded validation
- audit envelope
- semantic follow-up interpretation
- local transforms for presentation, sort/limit, dimension breakdown
- sibling-switch handling

Our preferred response policy:
- grounded facts first
- supporting table or numeric breakdown next
- concise business interpretation only when relevant and grounded
- no automatic recommendations in default factual answers
- deeper recommendations only when explicitly requested

Observed strengths:
- some payable/receivable answers are very good
- business interpretation can be useful
- local follow-ups can be fast

Observed problems:
- first-turn fresh queries are less reliable than follow-ups
- missing required filters like company/value_quantity on some requests
- some grounded answers are semantically wrong even though validation passes
- latency increased after adding more governance
- we may be tightening some areas too much while leaving other critical areas too loose

We do NOT want case-by-case keyword fixes.
We want system-level architecture guidance.

Please answer:
1. Is Qwen-Agent the right fit here?
2. What should Qwen-Agent own vs what should deterministic compiler/policy/validation own?
3. Is our semantic follow-up direction correct?
4. How should low-confidence follow-up handling work?
5. Should we build a FreshQueryCompilerContract next?
6. Since company is a single-company invariant, how should company be handled safely?
7. How much report-selection freedom should Qwen-Agent have?
8. How should we validate intent-to-result consistency, not just grounding?
9. How should we improve latency without losing enterprise control?
10. Are we over-tightening or under-governing in the wrong places?

Please structure your answer as:
- overall assessment
- what is correct
- what is risky/wrong
- recommended responsibility split
- recommended next implementation order
- Qwen-Agent-specific best practices for this architecture

Be specific and technical.
```

## How We Will Use The Answer

We will not blindly follow Qwen’s suggestions.

We will:

1. compare its advice against our enterprise contracts
2. keep only suggestions that improve:
   - governed correctness
   - follow-up reliability
   - latency/operability
   - clean responsibility boundaries

The goal is not to outsource design to Qwen.

The goal is to use Qwen as a specialized reviewer for the Qwen-Agent part of the system.
