# Libs – Step-by-Step Guide

> Planning artifacts go in `agents_plans/`.

## Steps
1. Plan in `agents_plans/tasks/`
2. Define TypeScript types in `types/`
3. Export via `index.ts` barrel files
4. Coordinate with consumers for breaking changes

## Key Types
- `Mention`: Core entity with sentiment, topics, metadata
- `AggregatedMetrics`: Time-windowed aggregates
- `FilterParams`: Common filter contract

