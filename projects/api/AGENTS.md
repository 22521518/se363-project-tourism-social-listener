# API – Step-by-Step Guide

> Planning artifacts go in `agents_plans/`.

## Steps

### Step 1: Plan
Create plan in `agents_plans/tasks/` before implementation.

### Step 2: Implement
```powershell
cd api && npm install && npm run dev
```
- Controllers: `<entity>.controller.ts` (thin handlers)
- Services: `<entity>.service.ts` (business logic)
- Repositories: `<entity>.repository.ts` (data access)

### Step 3: Test
```powershell
npm test
```

## Style
- TypeScript strict mode
- OpenAPI-first (define in `openapi.yaml` first)

## Commits
One controller/service/repository per commit.

