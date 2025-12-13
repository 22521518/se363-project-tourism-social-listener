# Data – Step-by-Step Guide

> Planning artifacts go in `agents_plans/`.

## Steps
1. Plan in `agents_plans/task/`
2. Add data files to appropriate folder
3. Document format changes in `agents_plans/`

## Locations
| Path | Content | Mutability |
|------|---------|------------|
| `raw/` | Original payloads | Immutable |
| `processed/` | Cleaned/normalized | Append-only |
| `models/` | Model artifacts | Versioned |

## Naming
- Raw: `<source>_<date>_<id>.json`
- Processed: `<pipeline>_<date>_<id>.json`
- Models: `<model>_v<version>.pkl`

