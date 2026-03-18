## Comparison Manual Execution Evidence

Date: 2026-03-18  
Owner: AI Runtime Engineering  
Scope: browser/manual execution evidence for the approved first implementation slice of `comparison`

### Environment Note
- Live app containers were restarted before the final manual verification pass.
- Fresh process confirmation was taken from the local Docker Compose stack (`backend`, `frontend`, `websocket`, `queue-short`, `queue-long`, `scheduler`).

### Manual Results Confirmed

1. Same-period territory comparison
- Prompt: `Compare Yangon and Mandalay sales last month by territory`
- Result: `Sales Analytics`
- Visible table:
  - `Territory | Yangon | Mandalay`
  - `Revenue | 6,306,500.00 | 8,680,000.00`
- Status: PASS

2. Same-period territory scale follow-up
- Prompt: `Show in Million`
- Result: `Sales Analytics`
- Visible table:
  - `Territory | Yangon | Mandalay`
  - `Revenue | 6.31 | 8.68`
- Status: PASS

3. Same-period correction rebind + scale follow-up
- Prompt sequence:
  - `Compare Yangon and Mandalay sales last month by territory`
  - `Actually compare Yangon and Bago instead`
  - `Show in Million`
- Result: `Sales Analytics`
- Visible table after correction:
  - `Territory | Yangon | Bago`
  - `Revenue | 6,306,500.00 | 0.00`
- Visible table after scale follow-up:
  - `Territory | Yangon | Bago`
  - `Revenue | 6.31 | 0.00`
- Status: PASS

4. Customer comparison
- Prompt: `Compare Shwe Li Road Mobile Wholesale and Latha Mobile Wholesale revenue last month`
- Result: `Customer Ledger Summary`
- Visible table:
  - `Customer | Shwe Li Road Mobile Wholesale | Latha Mobile Wholesale`
  - `Revenue | 0.00 | 0.00`
- Status: PASS (data-valid)
- Interpretation:
  - the visible shape is correct for `comparison`
  - the zero values are data-valid for the tested last-month scope, not a comparison-shaping defect

5. Supplier comparison
- Prompt: `Compare Sunflower Accessories Co. and Golden Dragon Trading Co. Ltd. purchase amount last month`
- Result: `Supplier Ledger Summary`
- Visible table:
  - `Supplier | Sunflower Accessories Co. | Golden Dragon Trading Co. Ltd.`
  - `Purchase Amount | 4,900,000.00 | 12,100,600.00`
- Status: PASS

6. Supplier scale follow-up
- Prompt: `Show in million`
- Result: `Supplier Ledger Summary`
- Visible table:
  - `Supplier | Sunflower Accessories Co. | Golden Dragon Trading Co. Ltd.`
  - `Purchase Amount | 4.90 | 12.10`
- Status: PASS

7. Item comparison
- Prompt: `Compare SPH-SAM-A15-6/128 and SPH-XMI-RN13-8/256 sales last month`
- Result: `Item-wise Sales Register`
- Visible table:
  - `Item | SPH-SAM-A15-6/128 | SPH-XMI-RN13-8/256`
  - `Revenue | 4,975,000.00 | 4,500,000.00`
- Status: PASS

8. Item scale follow-up
- Prompt: `show in million`
- Result: `Item-wise Sales Register`
- Visible table:
  - `Item | SPH-SAM-A15-6/128 | SPH-XMI-RN13-8/256`
  - `Revenue | 4.97 | 4.50`
- Status: PASS

9. Monthly period-vs-period comparison
- Prompt: `Compare Yangon revenue in March 2026 vs February 2026`
- Result: `Sales Analytics`
- Visible table:
  - `Territory | Feb 2026 | Mar 2026`
  - `Yangon | 6,306,500.00 | 5,817,000.00`
- Status: PASS

10. Monthly period-vs-period scale follow-up
- Prompt: `Show in Million`
- Result: `Sales Analytics`
- Visible table:
  - `Territory | Feb 2026 | Mar 2026`
  - `Yangon | 6.31 | 5.82`
- Status: PASS

11. Month-over-month comparison
- Prompt: `Show Yangon revenue month over month for March 2026`
- Result: `Sales Analytics`
- Visible table:
  - `Territory | Feb 2026 | Mar 2026`
  - `Yangon | 6,306,500.00 | 5,817,000.00`
- Status: PASS

12. Month-over-month scale follow-up
- Prompt: `Show in Million`
- Result: `Sales Analytics`
- Visible table:
  - `Territory | Feb 2026 | Mar 2026`
  - `Yangon | 6.31 | 5.82`
- Status: PASS

13. Clarification boundary
- Prompt: `Compare Yangon and Mandalay`
- Result:
  - `Which business measure should I use for the comparison (for example revenue or purchase amount)?`
- Status: PASS

14. Weekly unsupported boundary
- Prompt: `Compare Yangon revenue week over week`
- Result:
  - `I can't yet compare week over week in this class. Please ask for same-period, month-vs-month, or month-over-month comparison.`
- Status: PASS

15. Quarterly unsupported boundary
- Prompt: `Compare Yangon revenue quarter over quarter`
- Result:
  - `I can't yet compare quarter over quarter in this class. Please use same-period, month-vs-month, or month-over-month comparison for now.`
- Status: PASS

### Deferred Hardening Observation

1. Repeated scale follow-up on already-scaled period comparison is not idempotent yet
- Example sequence:
  - monthly comparison
  - `Show in Million`
  - repeated `Show in Million`
- Observed fallback:
  - `Metric | Value`
  - `revenue | 119,703,000.00`
- Assessment:
  - first scale follow-up is correct
  - repeated identical scale follow-up drifts to a generic total/KPI view
  - this is a follow-up hardening issue, not a failure of the approved core slice

### Manual Verdict

1. Approved `comparison` core slice behaviors are manually validated.
2. One repeated-transform idempotency variant remains as deferred hardening.
