# Phase 6 Confusion-Pair Scorecard

- Executed: 2026-02-22T13:41:47Z
- Baseline artifact: `/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260221T190025Z_phase1_first_run_baseline.json`
- Current artifact: `/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260222T120905Z_phase6_canary_uat_raw_v3.json`

## Wrong-Report Delta
- Baseline wrong-report rate: 0.0
- Current wrong-report rate: 0.0
- Relative improvement: 0.0
- Rule mode: baseline_zero_non_regression
- Gate pass: True

## Confusion-Pair Suite
- Suite: phase6_confusion_pairs_v1
- Total: 6
- Passed: 6
- Failed: 0
- Pass rate: 1.0
- Threshold: 0.95
- Gate pass: True

## P6 Exit Gate
- Wrong-report gate pass: True
- Confusion-pair gate pass: True
- Overall pass: True

## Case Results
- CP-01-payable-vs-receivable: pass=True | expected=Accounts Payable Summary | selected=Accounts Payable Summary | blockers=[]
- CP-02-receivable-vs-payable: pass=True | expected=Accounts Receivable Summary | selected=Accounts Receivable Summary | blockers=[]
- CP-03-sold-vs-received: pass=True | expected=Item-wise Sales Register | selected=Item-wise Sales Register | blockers=[]
- CP-04-received-vs-sold: pass=True | expected=Item-wise Purchase Register | selected=Item-wise Purchase Register | blockers=[]
- CP-05-customer-vs-supplier: pass=True | expected=Accounts Receivable Summary | selected=Accounts Receivable Summary | blockers=[]
- CP-06-supplier-vs-customer: pass=True | expected=Accounts Payable Summary | selected=Accounts Payable Summary | blockers=[]
