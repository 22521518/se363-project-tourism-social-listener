# Libs – Agent Guidelines

## Module Overview

Shared contracts and types used by all services and frontend.

## Code Style

- Use TypeScript for type definitions
- Export types via index.ts barrel files
- Keep types minimal and focused

## Key Types

Define these shared types:
- `Mention`: Core entity with sentiment, topics, metadata
- `AggregatedMetrics`: Time-windowed aggregates
- `FilterParams`: Common filter contract

## Commit Scope

- One type or interface change per commit
- Include migration notes for breaking changes
- Coordinate with consumers before modifying shared types
