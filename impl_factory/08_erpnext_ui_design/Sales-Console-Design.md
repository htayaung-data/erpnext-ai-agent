# Sales Console Design

Status: detailed workspace design for the first implementation target  
Scope: `Sales Console` only  
Source authority: [UI-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/UI-Design.md)

## 1. Purpose

This document defines the detailed design for the `Sales Console`.

It integrates three views together:

1. technical implementation view
2. ERP consultant view
3. real daily user view

The goal is to design a Sales Console that is:

1. easy to understand
2. simple in daily use
3. attractive without becoming flashy
4. enterprise-grade in structure and control
5. AI-assisted in a way that improves efficiency without overwhelming users

## 2. Sales Console Mission

The `Sales Console` should become the primary daily entry point for sales roles.

It should help sales users do five things well:

1. start the day fast
2. create and follow commercial documents with minimal friction
3. keep customer context visible
4. avoid missing approvals, blockers, and credit-risk signals
5. move from customer conversation to ERP action with fewer clicks

This console is not meant to be a full CRM replacement, a dashboard playground, or a generic selling module clone.
It is an operating cockpit for actual selling work.

## 3. Target Users

Primary users:

1. Sales Supervisor
2. Sales Executives
3. Key Account Sales

Secondary or occasional viewers:

1. General Manager for approval visibility
2. showroom-oriented sales users through a focused sales mode

## 4. Perspective Integration

### 4.1 ERP Consultant View

From an ERP consultant standpoint, the Sales Console must:

1. align with the sales quotation-to-order process
2. show workflow and approval status clearly
3. protect segregation of duties
4. keep selling roles inside their commercial scope
5. expose credit and approval issues early

### 4.2 Real User View

From the user standpoint, the Sales Console must:

1. feel like the shortest path to doing today’s work
2. reduce menu hunting
3. make it obvious which quotations, orders, or customers need attention now
4. help the user prepare before calling or meeting a customer
5. keep the screen clean enough to work fast all day

### 4.3 Technical Implementation View

From the implementation standpoint, the Sales Console must:

1. start with ERPNext-native workspace capabilities where possible
2. avoid unnecessary custom frontend complexity in the first release
3. support branch-aware and role-aware visibility
4. allow a compact AI assist layer without breaking the standard operating UI
5. be expandable later without redesigning the whole console

## 5. Business Outcomes

The Sales Console should improve:

1. quotation turnaround speed
2. order-entry efficiency
3. customer follow-up discipline
4. visibility of blocked or at-risk sales work
5. sales team adoption of role-based navigation instead of generic module browsing

## 6. Design Position

The Sales Console should feel:

1. customer-first
2. quotation-first
3. status-aware
4. approval-aware
5. branch-aware

It should not feel:

1. finance-heavy
2. stock-control-heavy
3. setup-heavy
4. report-only

## 7. Console Structure

The Sales Console should use this structure from top to bottom.

### 7.1 Header Zone

Contents:

1. workspace title: `Sales Console`
2. user identity and role-family label
3. branch context
4. optional assigned territory or sales scope
5. quick workspace search and quick action launcher

Purpose:

1. tell the user immediately where they are
2. show scope clearly
3. reduce context mistakes

### 7.2 Primary Actions Zone

This is the most important row in the console.

Primary actions:

1. `New Opportunity`
2. `New Quotation`
3. `New Sales Order`
4. `Open Customer`
5. `Open Item`

Rules:

1. these actions must be visible without scrolling
2. they should be large enough to scan quickly
3. they should be ordered by actual daily frequency, not by ERP module naming

### 7.3 Sales Work Queue Zone

This is the operational heartbeat of the console.

It should show:

1. quotations waiting for action
2. open quotations nearing expiry
3. sales orders pending fulfillment
4. orders blocked by approval
5. customer follow-up tasks
6. overdue or at-risk commercial items

This zone should feel like:

1. a work list
2. not just a report list

### 7.4 Operational Insight Zone

This zone should show lightweight commercial visibility, not a giant dashboard.

Suggested cards:

1. quotations awaiting approval
2. open orders
3. orders with credit-risk flags
4. customers needing follow-up today
5. branch sales snapshot
6. quotation-to-order conversion trend

### 7.5 Reports And Review Zone

This zone should provide quick access to deeper review surfaces.

Recommended reports:

1. `Sales Analytics`
2. `Customer-wise Sales History`
3. `Item-wise Sales Register`
4. `Open Orders`
5. quotation trend or open quotation review

### 7.6 AI Assist Zone

The AI zone must be present but visually restrained.

It should be:

1. right-side panel on wide screens or lower priority section on smaller screens
2. collapsible
3. context-aware
4. clearly secondary to the main operating UI

## 8. Real User Experience Flow

### 8.1 Morning Start

When a sales user lands on the console, they should understand within a few seconds:

1. what needs attention today
2. which quotations are aging
3. which orders are blocked
4. which customers need follow-up

### 8.2 Customer Call Or Visit

Before calling a customer, the user should be able to:

1. open the customer record quickly
2. see recent quotations and orders
3. see balance or credit warning context if relevant
4. get a compact AI-generated customer brief

### 8.3 Quotation Creation

The user should be able to:

1. start a quotation from the console directly
2. land in a simplified quotation form
3. see relevant customer and item context quickly
4. know whether the quotation will require approval

### 8.4 Follow-Up And Conversion

The user should be able to:

1. see which quotations deserve follow-up now
2. see which open orders are still pending action
3. move from customer context to quotation or order context without hunting through menus

## 9. AI Assist Design

The `Sales Console` is a high-value AI surface, but AI must remain tightly scoped.

### 9.1 Best AI Uses In Sales

Recommended AI functions:

1. customer briefing
   - recent orders
   - open quotations
   - overdue or credit context
2. quote-follow-up prioritization
   - which quotations deserve follow-up now
3. risk nudges
   - approval likely needed
   - credit-risk exposure
   - unusual discount situation
4. next-best-action suggestion
   - what should the sales user do next in this customer context

### 9.2 AI Uses To Avoid

Do not make AI:

1. the main path for creating quotations or orders
2. a full-page assistant
3. a chat box constantly asking the user what to do
4. a source of invisible pricing or approval decisions

### 9.3 AI Panel Behavior

The AI panel should support these modes:

1. `Today`
   - daily sales briefing
2. `Customer Context`
   - compact customer brief when a customer is selected
3. `Quotation Context`
   - approval/risk/follow-up explanation for the active quotation

The default state should be:

1. visible but compact
2. informative but not noisy

## 10. ERP Consultant Recommendations

From an ERP consultant perspective, these are the most important rules.

### 10.1 Scope Control

The Sales Console should:

1. keep sales users away from finance-heavy and stock-control-heavy navigation
2. expose only the stock visibility needed for selling
3. make branch and territory scope explicit

### 10.2 Approval Visibility

The Sales Console must show:

1. quotations requiring approval
2. orders blocked by credit or approval issues
3. escalated commercial cases

Sales users should never be confused about whether a document is still actionable by them or waiting on someone else.

### 10.3 Showroom Treatment

Do not build a separate standalone showroom workspace in the first phase.

Instead:

1. provide a showroom-focused mode inside `Sales Console`
2. simplify it further for counter-style speed
3. keep its stock visibility narrower than general sales users

## 11. Technical Implementation Recommendation

### 11.1 First Implementation Strategy

Start with ERPNext-native workspace capabilities plus minimal custom augmentation.

Phase 1 should use:

1. custom ERPNext workspace
2. curated shortcuts
3. curated report links
4. role-based visibility
5. lightweight custom cards or blocks where standard workspace blocks are not enough

Do not start with:

1. a fully custom single-page app
2. heavy frontend re-platforming
3. large visual rewrite before proving workflow value

### 11.2 Technical Composition

The Sales Console should likely be implemented as:

1. ERPNext workspace as the shell
2. shortcut section for primary actions
3. report section for deep review
4. custom summary widgets or dashboard cards for queue and blocker visibility
5. controlled AI assist panel or drawer integrated through the existing assistant stack

### 11.3 Required Data And UI Inputs

The console will need access to:

1. quotations by status
2. sales orders by status
3. customer follow-up indicators
4. branch-aware sales metrics
5. approval state
6. credit or balance warning context where permitted

### 11.4 Role Variants

The technical design should support role variants inside the same console:

1. Sales Supervisor
2. Sales Executive
3. Key Account Sales
4. showroom-focused sales user

The console shell should stay the same, but:

1. queue emphasis
2. metrics
3. approval visibility
4. AI hints

can vary by role.

## 12. Information Architecture Recommendation

Recommended top-level sections in the console:

1. `Quick Actions`
2. `My Sales Work`
3. `Approvals / Blockers`
4. `Customer Follow-Up`
5. `Sales Insight`
6. `AI Assist`

This is simpler and more understandable than exposing users to a large mixed dashboard of unrelated cards.

## 13. Visual Design Recommendation

The Sales Console should feel more polished than stock ERPNext, but still serious.

Recommended visual tone:

1. clean hierarchy
2. disciplined spacing
3. clear priority cards
4. restrained use of accent color
5. strong separation between:
   - actions
   - work queue
   - AI assist

The console should look modern and attractive, but the beauty should come from clarity and confidence, not decoration.

## 14. Success Criteria

The Sales Console is successful when:

1. sales users can start work faster than from generic ERPNext workspaces
2. users can find the right sales action in one click
3. follow-up obligations become harder to miss
4. approval blockers become obvious
5. AI improves preparation and prioritization without hijacking the UI

## 15. What Should Be Designed Next

Before implementation, the next detail layer for `Sales Console` should define:

1. exact workspace sections and card ordering
2. role-specific differences inside the console
3. showroom mode behavior
4. AI panel states and triggers
5. simplified quotation and sales order form behavior

## 16. Final Design Judgment

The `Sales Console` should be the first workspace implemented because it has the clearest business value and the clearest path to a better user experience.

If designed correctly, it will:

1. prove the role-based workspace strategy
2. improve adoption quickly
3. establish the standard for later consoles
4. demonstrate the right style of enterprise AI assistance
