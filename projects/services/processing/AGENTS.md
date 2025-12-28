# Processing – Step-by-Step Guide

> Planning artifacts go in `agents_plans/`.

## Steps

1. Plan in `agents_plans/tasks/`
2. Implement cleaner/normalizer as pure function
3. Test with edge cases

## Commands

```powershell
cd projects/services/processing && pip install -r requirements.txt && python -m pipelines.main
```

## Location Extraction Task

- Canonical LLM prompt (JSON-only) + Streamlit validation UI schema live here:
  - [tasks/location_extraction/README.md](tasks/location_extraction/README.md)
  - [tasks/location_extraction/AGENTS.md](tasks/location_extraction/AGENTS.md)
