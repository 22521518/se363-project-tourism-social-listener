# Processing – Agent Guidelines

## Module Overview

Reusable cleaning and normalization steps for the data pipeline.

## Commands

```powershell
cd services/processing
pip install -r requirements.txt
python -m pipelines.main
```

## Code Style

- Follow PEP 8
- Each cleaner/normalizer should be a pure function
- Document input/output formats

## Commit Scope

- One cleaner or normalizer per commit
- Include test cases with edge cases
- Document any format changes
