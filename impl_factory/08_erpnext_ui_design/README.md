# ERPNext UI Design Workstream

This folder is the managed home for the `feature/erpnext-ui-design` workstream.

Use it for:

1. raw UI references
2. working design notes
3. navigation, layout, and workspace exploration
4. design decisions and handoff material
5. future UI-specific implementation planning when explicitly created

Working rules:

1. do active UI work only from `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
2. verify the branch is `feature/erpnext-ui-design` before editing
3. keep UI-only notes inside `impl_factory/08_erpnext_ui_design/`
4. treat `main` as integration-only

Do not use this folder for:

1. AI Assistant runtime changes
2. assistant hardening work
3. edits to assistant-owned folders without coordination

Starter structure:

1. `references/`
2. `discovery/`
3. `navigation/`
4. `layout/`
5. `design-decisions/`
6. `handoff/`

Key note:

1. [UI-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/UI-Design.md)
2. [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md)
3. [Workspace-UI-Baseline-Reference.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Workspace-UI-Baseline-Reference.md)
4. [Sales-Console-Role-Permission-Matrix.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Role-Permission-Matrix.md)
5. [Sales-Console-Card-Definition-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Card-Definition-Spec.md)
6. [Sales-Console-UI-Layout-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-UI-Layout-Spec.md)
7. [Sales-Console-Customer-Inquiry-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Customer-Inquiry-Spec.md)
8. [Sales-Console-Navigation-Target-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Navigation-Target-Spec.md)
9. [Sales-Console-ERP-Capability-Audit.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-ERP-Capability-Audit.md)
10. [Sales-Console-Deferred-Tasks.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Deferred-Tasks.md)
11. [Sales-Console-Implementation-Plan.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Implementation-Plan.md)
12. [Sales-Order-Approval-Policy-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Order-Approval-Policy-Spec.md)
13. [Quotation-Approval-Policy-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Quotation-Approval-Policy-Spec.md)
14. [Sales-Console-Scenario-Catalog.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Catalog.md)
15. [Sales-Console-Scenario-Data-Requirements.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Data-Requirements.md)
16. [Sales-Console-Current-Data-Gap-Assessment.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Current-Data-Gap-Assessment.md)
17. [Sales-Console-Scenario-Seeding-Plan.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Scenario-Seeding-Plan.md)
18. [Sales-Console-Seed-Execution-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Seed-Execution-Spec.md)
19. [Sales-Console-Seed-Import-Manifest.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Seed-Import-Manifest.md)
20. [Sales-Console-Seed-Batch-Plan.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Seed-Batch-Plan.md)
21. [Sales-Console-Seed-Record-Blueprint.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Seed-Record-Blueprint.md)
22. [Sales-Console-Seed-Execution-Log.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Seed-Execution-Log.md)
23. [Sales-Console-Validation-Checkpoint.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Validation-Checkpoint.md)
24. [Child-Page-Design-Framework.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Child-Page-Design-Framework.md)
25. [Sales-Order-Page-Design-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Order-Page-Design-Spec.md)
26. [Quotation-Page-Design-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Quotation-Page-Design-Spec.md)
27. [Sales-Invoice-Page-Design-Spec.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Invoice-Page-Design-Spec.md)
28. [Sales-Console-Navigation-Map.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/navigation/Sales-Console-Navigation-Map.md)
29. [ui_workstream_handoff_2026-03-27.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/ui_workstream_handoff_2026-03-27.md)
