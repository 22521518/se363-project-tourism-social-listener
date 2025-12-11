# Aggregator – Agent Guidelines

## Module Overview

Workers that compute pre-aggregated metrics for fast dashboard queries.

## Commands

```powershell
cd services/aggregator
pip install -r requirements.txt
python main.py
```

## Code Style

- Follow PEP 8
- Use deterministic aggregation logic
- Include provenance (input time ranges) in outputs

## Output Format

Aggregates must include:
- `metricName`: identifier
- `timeWindow`: `{ start: ISO, end: ISO }`
- `groupBy`: dimension (e.g., sentiment, topic)
- `value`: computed metric

## Commit Scope

- One aggregate type per commit
- Include validation queries
- Document backfill procedures for new aggregates
