# Workspace UI Baseline Reference

Status: approved baseline visual reference for later workspace implementation  
Scope: shared workspace shell and card system for future ERPNext consoles  
Source authority: [UI-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/UI-Design.md), [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md)

## 1. Purpose

This document defines the baseline UI reference that later workspace pages should follow.

It exists so future pages do not need to re-decide the core visual language from scratch.

This document is:

1. a baseline for shell, surface, spacing, and card behavior
2. a practical implementation reference
3. a constraint against visual drift across workspaces

This document is not:

1. a fixed content template for every page
2. a fixed KPI template
3. a fixed card-definition authority
4. a replacement for page-specific business design

## 2. What This Baseline Covers

This baseline should be reused for:

1. workspace shell width and centering
2. section container styling
3. dark enterprise header treatment
4. KPI band styling approach
5. card surface language
6. icon tile treatment
7. shadow and border hierarchy
8. restrained accent behavior
9. action, queue, and report card relationship

This baseline should not blindly control:

1. exact card count
2. exact KPI formulas
3. exact workflow wording
4. exact role-specific emphasis
5. exact queue definitions
6. page-specific report selection

## 3. Baseline Design Judgment

The baseline visual tone should be:

1. enterprise-grade
2. premium but restrained
3. serious rather than playful
4. structured rather than decorative
5. role-oriented rather than module-oriented

The baseline should not feel:

1. flat and generic
2. consumer-dashboard styled
3. overly colorful
4. ornament-heavy
5. dependent on novelty effects

## 4. Source Reference Page

The current baseline is derived from the implemented `Sales Console`.

That page is the visual reference for:

1. section composition
2. card surface language
3. header treatment
4. icon treatment
5. shadow hierarchy
6. accent restraint

It is not the authority for:

1. sales-only KPIs
2. sales-only queue logic
3. sales-only report composition

## 5. Core Layout Rules

All major workspaces should follow this order:

1. dark context header
2. quick actions section
3. work queue section
4. insight or role-relevant review sections
5. reports and deeper review section
6. optional AI section

Layout rules:

1. the page should be centered inside a controlled content width
2. sections should be clearly separated by container depth, not by heavy borders
3. section headings should be simple and left aligned
4. section notes should remain short and secondary
5. spacing should do most of the hierarchy work

## 6. Header Baseline

The header should use:

1. a dark gradient shell
2. a strong workspace title
3. a compact KPI band inside the header
4. restrained inner contrast
5. clear textual KPI meaning

Header rules:

1. use the header as a summary area, not as a dashboard wall
2. keep KPI count limited to what the page can justify
3. do not copy the exact two-KPI structure blindly to every workspace
4. preserve dark-header authority even if KPI structure changes

## 7. Section Container Baseline

Section containers should use:

1. white or near-white surfaces
2. soft white border language
3. clear shadow separation from the page background
4. rounded corners that feel modern but not exaggerated
5. enough depth to separate sections before hover

Container rules:

1. section containers are the first depth layer
2. inner cards are the second depth layer
3. sub-boxes such as count modules are the third depth layer
4. do not use decorative corner effects to create separation

## 8. Card Surface Baseline

Card surfaces should follow these rules:

1. white card body
2. white-based border, not hard grey by default
3. premium shadow hierarchy
4. hover should strengthen confidence, not create a dramatic animation
5. accent use should stay narrow and purposeful

Card rules:

1. use stronger depth hierarchy before adding more color
2. avoid gradient overlays on full card bodies unless there is a justified exception
3. small internal modules should remain visually subordinate
4. borders should support clarity, not become the main design language

## 9. Quick Actions Baseline

Quick action cards should feel:

1. immediate
2. clickable
3. slightly more active than reports
4. easy to scan at a glance

Quick action visual rules:

1. stronger icon presence is allowed
2. accent strip may be slightly stronger than report cards
3. card depth may be slightly stronger than report cards
4. keep wording short and action-oriented

## 10. Work Queue Baseline

Work queue cards should feel:

1. operational
2. structured
3. work-list driven
4. serious and actionable

Queue rules:

1. queue cards may use side-count modules when the page is genuinely queue-heavy
2. side-count boxes are acceptable but are not a universal rule for every workspace
3. one priority or blocker card may receive modest emphasis
4. emphasis should come from hierarchy and structure before visual decoration
5. status wording must remain business-meaningful

## 11. Reports And Review Baseline

Report cards should feel:

1. calmer than quick actions
2. still first-class, not weak
3. review-oriented rather than action-urgent

Report rules:

1. report cards should share the same family as action cards
2. report cards should be slightly quieter in accent and icon emphasis
3. do not flatten report cards so much that they look underpowered
4. keep report CTA treatment simple and secondary

## 12. Icon System Baseline

Icon tiles should follow these rules:

1. use dark muted icon containers
2. use light icons inside
3. keep icon tile sizing consistent across card families unless there is a strong reason not to
4. use business-appropriate icons rather than generic placeholders

Icon rules:

1. action and report icons can share the same size
2. report icon emphasis may be slightly calmer than action icon emphasis
3. icon meaning should help scanning, not decorate empty space
4. do not allow icon families to drift page by page

## 13. Accent Behavior Baseline

Accent behavior should be restrained.

Allowed accent behaviors:

1. header gradient atmosphere
2. narrow top accent strips
3. narrow left emphasis rails for priority or queue states
4. very limited status-pill color use

Avoid:

1. full bright bars across many cards
2. decorative corner highlights
3. large card-surface gradients
4. random accent changes between pages

## 14. Reuse Rules For Future Pages

Future pages should reuse:

1. shell width and spacing logic
2. header style family
3. section container depth
4. card surface language
5. icon tile language
6. border and shadow hierarchy
7. restrained hover logic

Future pages may adapt:

1. KPI quantity and structure
2. queue layout pattern
3. emphasis level by role
4. action-to-report ratio
5. page-specific card definitions
6. business labels and status text

## 15. Implementation Guardrails

When building new workspace pages:

1. start from this baseline before inventing a new visual pattern
2. only introduce a new card variant when the business meaning truly needs it
3. prefer structural hierarchy over decorative styling
4. prefer consistency over novelty
5. if a new page needs stronger variation, document why

## 16. Final Baseline Decision

This baseline is approved as the shared visual reference for future workspace implementation.

The rule is:

1. reuse the system
2. do not duplicate the sales page literally
3. adapt business content without drifting from the visual language
4. escalate only when a future workspace has a real structural reason to diverge
