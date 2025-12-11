# NLP – Step-by-Step Guide

> Planning artifacts go in `agents_plans/`.

## Steps
1. Plan in `agents_plans/task/`
2. Implement enrichment (idempotent)
3. Test with evaluation metrics

## Commands
```powershell
cd services/nlp && pip install -r requirements.txt && python main.py
```

## Output Format
- `language`: ISO code
- `sentiment`: `{ label, score }`
- `topics`: array
- `entities`: extracted entities

