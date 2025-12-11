# Data – Agent Guidelines

## Module Overview

Dataset storage for development, testing, and experiments.

## Data Locations

| Path | Content | Mutability |
|------|---------|------------|
| `raw/` | Original payloads | Immutable |
| `processed/` | Cleaned/normalized | Append-only |
| `models/` | Model artifacts | Versioned |

## File Naming

- Raw: `<source>_<date>_<id>.json`
- Processed: `<pipeline>_<date>_<id>.json`
- Models: `<model>_v<version>.pkl`

## Commit Scope

- Document data format changes in `agents_plans/`
- Include sample files for new formats
- Keep samples small (< 1MB)
