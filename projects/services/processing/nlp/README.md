# NLP Service

Enriches raw messages with semantic signals: sentiment, topics, entities, and classifications.

## Purpose

- Detect language
- Analyze sentiment (positive/neutral/negative)
- Extract topics and named entities
- Classify tourism intent
- Extract locations (geo entities) for downstream enrichment

## Technology

- **Language**: Python
- **NLP**: LLM (provider configurable), spaCy, VADER
- **Models**: DistilBERT, RoBERTa (fallback)

## Status

🚧 _Scaffolded — enrichment pipelines to be implemented_

## Location Extraction

Location extraction is specified as a production-ready contract (JSON-only LLM output) with DB-first persistence and Streamlit validation UI.

See: [../task/location_extraction/README.md](../task/location_extraction/README.md)
