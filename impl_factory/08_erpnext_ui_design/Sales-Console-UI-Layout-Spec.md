# Sales Console UI Layout Spec

Status: detailed layout, hierarchy, and first-look behavior spec for `Sales Console`  
Scope: section order, prominence, compact states, expansion rules, and role-based default behavior  
Source authority: [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md), [Sales-Console-Role-Permission-Matrix.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Role-Permission-Matrix.md), [Sales-Console-Card-Definition-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Card-Definition-Spec.md)

## 1. Purpose

This document defines how the `Sales Console` should be organized so it remains powerful without becoming overwhelming.

It answers:

1. what should be fully visible on first load
2. what should remain compact by default
3. what should expand only on demand or context
4. how the layout should vary by role

## 2. Core Layout Principle

The layout must follow this rule:

1. first look should answer only the most urgent daily questions
2. deeper surfaces should appear lower, quieter, or contextually
3. the page must not expose every important feature at equal visual weight

This console should use:

1. intent-based grouping
2. progressive disclosure
3. role-based emphasis
4. contextual expansion

It should not rely on:

1. many equal-weight sections
2. collapse-only design as the main organizing method
3. document-type-first grouping

## 3. Default Section Order

The default order is:

1. `Header And Summary`
2. `Quick Actions`
3. `Customer Inquiry`
4. `My Sales Work`
5. `Customer Lifecycle Visibility`
6. `Approvals / Blockers`
7. `Reports And Review`
8. `AI Assist`

This is the baseline reference layout.

## 4. Section Weight Model

Each section must be assigned one of four states:

1. `Primary`
   - fully visible
   - strong headline treatment
2. `Secondary`
   - visible but compact
3. `On-Demand`
   - shown in lower-emphasis or expandable state
4. `Contextual`
   - expands only when user action or live data makes it relevant

## 5. First-Look Behavior On Page Load

### 5.1 Always Primary On First Load

These should be immediately visible and readable:

1. `Header And Summary`
2. `Quick Actions`
3. `Customer Inquiry`
4. `My Sales Work`

Reason:

1. these areas answer the daily questions:
   - what should I do
   - what should I find
   - what work needs attention

### 5.2 Secondary On First Load

These should appear, but less prominently:

1. `Customer Lifecycle Visibility`
2. `Approvals / Blockers`

Reason:

1. they are important
2. but they should not compete visually with daily action and inquiry on first view

### 5.3 Quieter On First Load

These should appear lower and calmer:

1. `Reports And Review`
2. `AI Assist`

Reason:

1. they are important supporting surfaces
2. but they should not dominate the page entry experience

## 6. Section-by-Section First-Look Rules

### 6.1 Header And Summary

Default state:

1. fully visible
2. compact KPI band only

Rules:

1. do not overload with many KPI cards
2. maximum 2 visible summary cards in first wave
3. any additional summary signal should go below as lifecycle or blocker cards

### 6.2 Quick Actions

Default state:

1. fully visible
2. all five cards shown

Rules:

1. no collapse on desktop in first view
2. action cards should be the easiest scanning zone on the page

### 6.3 Customer Inquiry

Default state:

1. input bar fully visible
2. result area compact or empty until search

When inactive:

1. show input and short guidance only

When active:

1. expand into the main inquiry result surface

This is a key contextual section.

### 6.4 My Sales Work

Default state:

1. fully visible
2. top four queue cards visible

Rules:

1. keep this section operational and scanable
2. do not bury it under review-heavy content

### 6.5 Customer Lifecycle Visibility

Default state:

1. visible
2. compact card row

Expansion triggers:

1. user opens one card
2. inquiry result links to downstream status
3. live counts are non-zero and need attention

### 6.6 Approvals / Blockers

Default state:

1. visible
2. compact for `Sales Person`
3. stronger for `Sales Manager` and `Executive Approver`

Expansion triggers:

1. blocked items exist
2. approval queue count is non-zero
3. current role is review-heavy

### 6.7 Reports And Review

Default state:

1. visible
2. quieter styling
3. limited visible cards

Rules:

1. avoid large report catalog at first look
2. show only a small set of best review targets

### 6.8 AI Assist

Default state:

1. visible but compact
2. should not visually compete with inquiry or work queue

Expansion triggers:

1. inquiry result exists
2. active quotation/order context exists
3. user explicitly opens AI detail

## 7. Role-Based First-Look Variants

### 7.1 Sales Person

Primary:

1. `Quick Actions`
2. `Customer Inquiry`
3. `My Sales Work`

Secondary:

1. `Customer Lifecycle Visibility`
2. `Approvals / Blockers`

Quieter:

1. `Reports And Review`
2. `AI Assist`

### 7.2 Sales Manager

Primary:

1. `Approvals / Blockers`
2. `Customer Inquiry`
3. `My Sales Work`

Secondary:

1. `Customer Lifecycle Visibility`
2. `Reports And Review`

Quieter:

1. `Quick Actions`
2. `AI Assist`

### 7.3 Executive Approver

Primary:

1. `Approvals / Blockers`
2. `Header And Summary`

Secondary:

1. `Customer Inquiry`
2. `Reports And Review`

Quieter:

1. `Quick Actions`
2. `My Sales Work`
3. `Customer Lifecycle Visibility`

## 8. Progressive Disclosure Rules

### 8.1 Do Not Expose Equal Weight Everywhere

Important features may all exist, but they must not all look equally urgent.

### 8.2 Use Contextual Expansion

Examples:

1. inquiry result expands after search
2. approvals become more visible when blocked items exist
3. AI becomes richer when a customer or order is selected
4. lifecycle section gains prominence when active delivery, payment, or return issues exist

### 8.3 Use Compact Containers For Lower-Priority Areas

Examples:

1. reports stay calmer than actions
2. AI stays calmer than inquiry
3. lifecycle remains grouped rather than scattered into many isolated cards

## 9. Organization By User Intent

The console should be understood by intent, not by ERP table names.

Recommended mental model:

1. `Do`
   - `Quick Actions`
2. `Find / Answer`
   - `Customer Inquiry`
3. `Work`
   - `My Sales Work`
4. `Track`
   - `Customer Lifecycle Visibility`
5. `Resolve`
   - `Approvals / Blockers`
6. `Review`
   - `Reports And Review`
7. `Assist`
   - `AI Assist`

This should be reflected in visual ordering and section wording.

## 10. What To Avoid

Avoid these patterns:

1. many collapsible sections as the main UX strategy
2. too many KPI cards above the fold
3. too many document-type zones
4. making reports as visually strong as actions
5. making AI as visually strong as inquiry

## 11. First-Wave Layout Recommendation

The best first-wave organization is:

1. keep the top of the page simple
2. make inquiry one of the strongest sections
3. group downstream visibility in one dedicated lifecycle section
4. keep reports calm
5. keep AI compact until context exists

## 12. Final Layout Judgment

The page should feel:

1. guided
2. calm
3. sales-first
4. customer-aware
5. operationally strong

The right measure of success is not how many features are visible immediately.
It is how quickly the user can understand:

1. what to do
2. what to search
3. what is blocked
4. what to tell the customer
