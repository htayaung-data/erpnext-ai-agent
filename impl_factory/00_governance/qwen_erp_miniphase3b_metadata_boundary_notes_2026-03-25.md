# Qwen ERP Mini-phase 3B Metadata Boundary Notes

Date: 2026-03-25

## Purpose

Clarify which metadata surfaces are intended to be canonical enterprise semantics and which remain transitional surface hints during the current migration.

## Canonical Metadata

These should express stable business meaning and governed support:

- business ontology `concept_id`
- business ontology canonical aliases
- report family `ontology_concepts`
- capability `ontology_concepts`
- report family / capability / report relationships
- supported intent classes
- default intent class

## Transitional Metadata

These may still exist during the migration, but they are not semantic authority:

- report family `intent_markers`
- business ontology `extended_aliases`
- other phrase-surface hints used only to help clarification or fallback ranking

## Engineering Rule

- Canonical metadata may drive governed domain detection and capability/family alignment.
- Transitional metadata may assist ambiguity handling or candidate ranking.
- Transitional metadata must not become the sole authority for business routing when canonical signals are absent.

## Current Mini-phase 3B Direction

- capability ontology surfaces were normalized toward canonical concept IDs
- supported ontology detection now operates on canonical concepts directly
- phrase-surface markers are explicitly treated as transitional in code
- report family `intent_markers` were trimmed where they only duplicated canonical ontology or report-name surface

## Remaining 3B Work

- review overly broad ontology aliases that may behave more like product wording than canonical business semantics
- review remaining `intent_markers` inventory and trim entries that are rescuing specific phrasings rather than expressing durable business surface
