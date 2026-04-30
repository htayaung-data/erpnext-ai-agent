# Qwen ERP Discovery Foundation Note

Date: 2026-03-25

## Purpose

Mini-step Group 1 introduces a separate discovery foundation for ERP metadata.

This is intentionally **not** a runtime-routing change.

It exists to:

1. extract real ERP report and doctype surface from the live ERP
2. save that surface as a snapshot
3. keep discovered surface separate from governed metadata
4. prepare for later evaluation before any contract or runtime integration

## What Was Added

1. Discovery exporter module:
   - [erp_metadata_discovery.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/erp_metadata_discovery.py)

2. Discovery snapshot directory:
   - [README.md](/home/deploy/erp-projects/erpai_project1/impl_factory/01_discovery/qwen_enterprise_metadata_snapshots/README.md)

## Current Scope

The discovery snapshot currently exports:

1. ERP reports:
   - report name
   - module
   - ref doctype
   - report type
   - standard/custom signal
   - roles
   - report-defined filters
   - report-defined columns

2. Referenced doctypes:
   - doctype identity
   - module
   - table/custom flags
   - title/search fields
   - field surface

3. ERP-wide doctype summary:
   - all doctypes with lightweight summary

4. Governed alignment summary:
   - governed reports present in ERP
   - governed reports missing from ERP

## Important Boundary

This discovery layer is:

- descriptive
- snapshot-based
- non-authoritative for runtime

It is **not**:

- automatic promotion into governed metadata
- direct runtime routing policy
- semantic compatibility logic

## Intended Next Decision

After generating and inspecting real snapshots, we decide whether Group 2 is justified:

1. change detection / diff awareness
2. manual refresh command and operating model
3. later, only if still justified:
   - promotion boundary
   - compatibility contracts
   - runtime integration

## Current Evaluation

The first live snapshot already showed real value:

1. 219 ERP reports were discovered
2. 963 doctypes were discovered
3. 73 referenced doctypes were material to the discovered report surface
4. 1 governed report name currently in runtime metadata is missing from live ERP:
   - `Sales Invoice List`

It also exposed an important limit:

1. many Script Reports do not expose useful columns/filters through the `Report` doc itself

That result was strong enough to justify a small Group 2 addition:

1. source signature
2. snapshot diff
3. refresh-if-changed helper
4. lightweight discovery evaluation summary export

It was **not** strong enough to justify runtime integration yet.

## Discovery Strengthening Slice

One additional discovery-strengthening slice was added after the first evaluation:

1. discovered reports now carry `surface_sources`
2. script reports with no ERP-declared filters/columns can still expose governed surface hints when:
   - the live ERP report name matches a governed report registry entry

This keeps the boundary clear:

1. live ERP declaration remains distinct from governed registry hints
2. discovery is more useful for evaluation
3. runtime still does not consume discovery directly
