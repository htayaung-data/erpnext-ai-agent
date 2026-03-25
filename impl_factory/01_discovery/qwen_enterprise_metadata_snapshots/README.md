# Qwen ERP Discovered Metadata Snapshots

This directory is for auto-extracted ERP surface snapshots.

Purpose:

1. keep discovered ERP metadata separate from curated governed metadata
2. let the team inspect real ERP report and doctype surfaces before changing runtime policy
3. support future diff/version-triggered refresh without coupling discovery directly to runtime decisions

Current foundation:

1. `latest_discovered_erp_surface.json` is the most recent exported discovery snapshot
2. timestamped `discovered_erp_surface_*.json` files are immutable point-in-time exports
3. snapshots now carry a `source_signature` for:
   - `Report`
   - `DocType`
   - `Custom Field`
   - `Property Setter`

Current utilities:

1. export current snapshot
2. refresh only when source signature changes
3. diff snapshots for:
   - added/removed reports
   - changed report identity metadata
   - added/removed doctypes
   - changed doctype summary metadata
4. export a lightweight discovery evaluation summary:
   - `latest_discovery_evaluation_summary.json`
   - `latest_discovery_evaluation_summary.md`
5. discovered reports now preserve surface provenance:
   - `erp_report_doc`
   - `governed_registry`

Meaning:

- `erp_report_doc` = declared directly in live ERP `Report` metadata
- `governed_registry` = governed hints from curated Qwen metadata for matching live report names

Important boundary:

- files here are **discovered ERP surface**
- files in `impl_factory/03_config/qwen_enterprise_metadata/` remain **governed runtime metadata**
- discovery does not automatically promote into governed policy
