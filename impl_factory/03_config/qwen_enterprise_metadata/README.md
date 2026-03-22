# Qwen Enterprise Metadata

This directory is the shared metadata source of truth for the Qwen ERP assistant path.

It is intentionally separated from runtime code so that:

1. ERP-side follow-up logic can read the same metadata as runtime policy
2. report/capability approval is governed as data, not scattered code
3. future multilingual, artifact, and write-safety layers can extend the same structure

Deployment note:

1. ERP Python services should mount this directory read-only and expose it through `QWEN_ENTERPRISE_METADATA_DIR`
2. the external Qwen runtime should mount the same directory read-only
3. ERP-side and runtime-side code should read this directory as configuration, not copy it into code-local JSON files

Current files:

1. `capability_registry.json`
2. `report_registry.json`
3. `report_family_registry.json`
4. `business_ontology.json`
5. `validation_rules.json`
