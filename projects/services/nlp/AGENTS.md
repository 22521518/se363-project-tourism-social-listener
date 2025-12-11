# NLP – Agent Guidelines

## Module Overview

Enrichment workers that add semantic signals to raw messages.

## Commands

```powershell
cd services/nlp
pip install -r requirements.txt
python main.py
```

## Code Style

- Follow PEP 8
- Use type hints for all functions
- Make enrichment pipelines idempotent (safe to re-run)

## Output Format

Enriched mentions must include:
- `language`: ISO code (e.g., "vi", "en")
- `sentiment`: `{ label: "POS"|"NEU"|"NEG", score: float }`
- `topics`: array of topic strings
- `entities`: extracted named entities

## Commit Scope

- One enrichment type per commit (sentiment, topics, etc.)
- Include evaluation metrics for model changes
- Document model versions in commit messages
