# API – Agent Guidelines

## Module Overview

Delivery layer exposing stable endpoints for mentions, aggregates, and metadata.

## Commands

```powershell
# Install and run (when implemented)
cd api
npm install
npm run dev
```

## Code Style

- Use TypeScript with strict mode
- Follow OpenAPI-first: define endpoints in `openapi.yaml` before implementing
- Controllers: thin handlers, delegate to services
- Services: business logic, testable functions
- Repositories: data access only, no business rules

## File Naming

- Controllers: `<entity>.controller.ts`
- Services: `<entity>.service.ts`
- Repositories: `<entity>.repository.ts`

## Testing

```powershell
npm test
```

## Commit Scope

- One controller/service/repository change per commit
- Include request/response examples for API changes
- Document breaking changes in `agents_plans/`
