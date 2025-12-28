# Processing Service

Data cleaning, normalization, and transformation pipelines.

## Structure

| Folder         | Purpose                       |
| -------------- | ----------------------------- |
| `cleaners/`    | Text cleaning utilities       |
| `normalizers/` | Format normalization          |
| `nlp/`         | NLP-specific processing       |
| `pipelines/`   | Composed processing workflows |

## Location Extraction

This repo treats location extraction as a task-scoped processing pipeline with:

- Canonical unified input DTO only (`UnifiedTextEvent`)
- JSON-only extraction contract (LLM or rule-based)
- DB persistence first; Kafka emitted only after commit
- Human validation supported via a DB-backed UI (agent contains no UI logic)
- Provider-agnostic LLM integration (no hardcoded vendors)

See: [tasks/location_extraction/README.md](tasks/location_extraction/README.md)

## Purpose

- Clean and sanitize raw text
- Normalize formats and timestamps
- Prepare data for enrichment

## Status

🚧 _Scaffolded — pipelines to be implemented_
