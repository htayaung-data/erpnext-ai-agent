# Deferred UI Improvements

Date created: 2026-04-16

Purpose:

- record non-blocking UI and UX work that should be handled later
- avoid reopening frozen pages for small aesthetic churn
- keep future polish tied to measured business value

Status rule:

- items in this file are deferred, not forgotten
- do not reopen frozen pages unless an item has a clear owner, scope, and validation method

## Priority 1: Draft performance and stability

### 1. Reduce draft-body reveal time

Current state:

- New Quotation and New Sales Order usually reveal usable body content in about 3 to 5 seconds

Target:

- reduce average reveal time without reintroducing flashing or unstable swaps

Notes:

- performance work must be measurement-first
- do not remove guardrails that prevent regression just to make the page appear faster

### 2. Keep draft state from re-entering preparation

Current state:

- major regression is fixed
- still needs periodic validation after future runtime changes

Target:

- draft body should enter preparation once, then reveal once, then remain stable

### 3. Keep native field mutations invisible to the user

Current risk:

- Frappe can briefly expose native field structure before productized layout is fully ready

Target:

- no visible label swapping
- no temporary native blocks such as unexpected activity areas before productized body is ready

## Priority 2: Visual rhythm and spacing

### 4. Normalize section-band spacing

Current state:

- some section containers feel slightly tighter or wider than neighboring sections

Target:

- consistent vertical rhythm between:
  - header summary
  - readiness band
  - tabs
  - body sections

Rule:

- solve at shared layout level, not page-by-page

### 5. Normalize content width rhythm

Current state:

- some inner cards align well, but a few sections still feel optically wider or narrower than adjacent blocks

Target:

- common container rules for:
  - snapshot blocks
  - commercial summary blocks
  - optional context blocks
  - tables and their action rows

## Priority 3: Draft form usability

### 6. Review Draft Readiness density after broader rollout

Current state:

- Draft Readiness is useful and should stay
- current treatment is intentionally lighter than earlier versions

Future check:

- confirm it stays support-level, not dominance-level, after more forms adopt the same pattern

### 7. Re-evaluate optional tax guidance after more real usage

Current state:

- tax is demoted and now behaves more appropriately for common sales draft work

Future check:

- confirm whether sales users actually need more guidance for:
  - template choice
  - exceptions
  - country/company-specific tax defaults

## Priority 4: Cross-page consistency

### 8. Final spacing consistency pass across all completed sales pages

Pages included:

- Sales Console
- Sales Order
- Quotation
- Delivery Note
- Sales Invoice
- New Quotation
- New Sales Order

Goal:

- one final consistency pass after the broader Sales Console scope is complete

Reason:

- this is lower risk and more efficient than repeated page-by-page micro-fixes now

### 9. Performance validation across all child pages

Goal:

- confirm that child-page mount, navigation, and top-of-page landing remain stable across all finalized pages

Focus:

- loading behavior
- scroll landing position
- action-card navigation feedback
- no native-content flash before productized layout

## Not deferred: do immediately if broken

These are not backlog polish items. Fix immediately if they regress:

- customer lookup not selectable
- item lookup not selectable
- price list no longer reflects live selling price lists
- delete row behavior broken
- draft body reopens preparation after reveal
- shared runtime divergence between New Quotation and New Sales Order

## Decision rule for future work

Before implementing any item from this file, confirm:

1. Is it solving a real business-use or usability problem?
2. Is the fix shared and scalable, not local and decorative?
3. Can we verify it with measurement, screenshots, or a clear interaction test?

If the answer is no, leave it deferred.
