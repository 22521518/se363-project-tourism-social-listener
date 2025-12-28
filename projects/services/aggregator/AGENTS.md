# Aggregator – Step-by-Step Guide

> Planning artifacts go in `agents_plans/`.

## Steps
1. Plan in `agents_plans/tasks/`
2. Implement aggregate worker
3. Test with validation queries

## Commands
```powershell
cd services/aggregator && pip install -r requirements.txt && python main.py
```

## Output Format
- `metricName`: identifier
- `timeWindow`: `{ start: ISO, end: ISO }`
- `groupBy`: dimension (e.g., sentiment, topic)
- `value`: computed metric

