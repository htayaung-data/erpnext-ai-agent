# Incident Register Template

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: template for Phase 3 incident tracking and incident-to-regression closure

## Purpose
Use this template for every Tier 1 and Tier 2 incident.

The goal is to make closure evidence consistent and to ensure every important failure leaves behind permanent regression protection.

## Incident Header

- Incident ID:
- Date Opened:
- Severity: `P1` / `P2` / `P3`
- Risk Tier: `Tier 1` / `Tier 2` / `Tier 3`
- Owner:
- Status: `Open` / `In Progress` / `Blocked` / `Closed`

## User-Visible Symptom

- User prompt or flow:
- Browser/replay environment:
- What the user saw:
- Expected behavior:

## Classification

- Behavioral class:
- Primary incident family:
  - `class selection failure`
  - `resolver/report selection failure`
  - `state carryover / topic authority failure`
  - `transform-followup failure`
  - `projection/shaping failure`
  - `quality-gate misclassification`
  - `write-safety failure`
  - `browser/replay parity failure`
  - `capability metadata gap`
  - `ontology normalization gap`

## Root Cause

- Root-cause summary:
- Violated class invariant:
- Shared surfaces impacted:
  - `resolver`
  - `memory/state`
  - `spec_pipeline`
  - `transform_last`
  - `response_shaper`
  - `quality_gate`
  - `latest-record flow`
  - `write path`
  - `browser/runtime parity`

## Fix Record

- Fix summary:
- Files changed:
- Why the fix stays inside contract boundary:

## Regression Assets Added

- Unit/module regression:
- Replay evidence:
- Browser/manual evidence:
- Variation-matrix row updated:

## Reruns Performed

- Targeted reruns:
- Shared-surface reruns:
- Browser/manual reruns:
- Release gate rerun required: `Yes` / `No`

## Evidence Links

- Raw replay log(s):
- Browser/manual screenshots or notes:
- Release gate output, if applicable:

## Closure Decision

- Closure date:
- Closed by:
- Why this incident is considered closed:
- Residual risk, if any:

## Notes

- Follow-up governance action:
- Future class/metadata/ontology update needed:
