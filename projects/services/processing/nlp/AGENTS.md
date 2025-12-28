# NLP – Step-by-Step Guide

> Planning artifacts go in `agents_plans/`.

## Steps

1. Plan in `agents_plans/tasks/`
2. Implement enrichment (idempotent)
3. Test with evaluation metrics

## Output Format

- `language`: ISO code
- `sentiment`: `{ label, score }`
- `topics`: array
- `entities`: extracted entities

## Location Extraction

- JSON-only extraction prompt + schema (LLM contract): [../tasks/location_extraction/README.md](../tasks/location_extraction/README.md)
- Implementation workflow + DoD: [../tasks/location_extraction/AGENTS.md](../tasks/location_extraction/AGENTS.md)
