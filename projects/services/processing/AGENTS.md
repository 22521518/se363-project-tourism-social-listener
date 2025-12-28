# Processing – Step-by-Step Guide

> Planning artifacts go in `agents_plans/`.

## Steps

1. Plan in `agents_plans/task/`
2. Implement cleaner/normalizer as pure function
3. Test with edge cases

## Commands

```powershell
cd projects/services/processing && pip install -r requirements.txt && python -m pipelines.main
```

## Location Extraction Task

- Canonical LLM prompt (JSON-only) + Streamlit validation UI schema live here:
  - [task/location_extraction/README.md](task/location_extraction/README.md)
  - [task/location_extraction/AGENTS.md](task/location_extraction/AGENTS.md)
