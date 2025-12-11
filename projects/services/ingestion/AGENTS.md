# Ingestion – Agent Guidelines

## Module Overview

Platform connectors that collect raw social media data.

## Commands

```powershell
cd services/ingestion
pip install -r requirements.txt
python main.py
```

## Code Style

- Follow PEP 8
- Use async/await for I/O operations
- Handle rate limits with exponential backoff

## Output Format

Raw messages must include:
- `source`: platform name (e.g., "youtube")
- `externalId`: platform-specific ID
- `rawText`: original content
- `createdAt`: ISO timestamp
- `rawPayload`: full API response

## Commit Scope

- One connector per commit
- Include sample output in `data/raw/`
- Document rate limits and recovery steps
