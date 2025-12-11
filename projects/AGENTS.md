# AGENTS.md – Agent Guidelines

This file provides operational guidelines for coding agents working on the Social Listening project. For human-oriented documentation, see `README.md`.

---

## Project Overview (Agent Perspective)

**Purpose:** Build an event-driven social listening pipeline that collects, enriches, and surfaces sentiment insights for tourism conversations.

**Current state:**
- Streamlit dashboard is the only working code (`frontend/web/streamlit/`)
- Module folders have `README.md` and `AGENTS.md` for domain-specific guidance
- Architecture is documented but implementation is in early stages

---

## Build & Run Commands

### Streamlit Dashboard

```powershell
cd frontend/web/streamlit
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Python Virtual Environment (Recommended)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Future Services (when implemented)

```powershell
# API service (Node.js)
cd api && npm install && npm run dev

# Python workers
cd services/<worker> && pip install -r requirements.txt && python main.py
```

---

## Code Style Guidelines

### Python
- Follow PEP 8
- Use type hints for function signatures
- Prefer `snake_case` for functions and variables
- Use docstrings for public functions

### TypeScript/JavaScript
- Use ESLint with project config
- Prefer `camelCase` for functions/variables, `PascalCase` for classes/components
- Use TypeScript strict mode

### General
- Keep functions focused and small
- Add meaningful comments for non-obvious logic
- Handle errors explicitly (no silent failures)

---

## Testing Instructions

### Unit Tests

```powershell
# Python (when pytest is configured)
cd <module>
pytest tests/

# Node.js (when jest is configured)
cd <module>
npm test
```

### Integration Testing
- Use local PostgreSQL with test data
- Verify Streamlit dashboard loads and displays data correctly

---

## Module Organization

| Directory           | Purpose                                      |
|---------------------|----------------------------------------------|
| `api/`              | REST API endpoints (delivery layer)          |
| `api/controllers/`  | Request handlers                             |
| `api/entities/`     | Domain entity definitions                    |
| `api/repositories/` | Data access layer                            |
| `api/services/`     | Business logic                               |
| `data/`             | Data storage (raw, processed, models)        |
| `frontend/`         | UI components and dashboards                 |
| `libs/types/`       | Shared TypeScript types and contracts        |
| `services/ingestion/` | Social platform connectors               |
| `services/nlp/`     | Sentiment, topics, embeddings                |
| `services/processing/` | Data cleaning and normalization          |
| `services/aggregator/` | Metrics computation                      |
| `agents_plans/`     | Work planning and tracking                   |

---

## Commit Guidelines

### Commit Scope
- **Each commit should be minimal and scoped to a single function, module, or logic unit**
- Avoid large commits that span entire domains
- One logical change per commit

### Commit Message Format

```
<type>(<scope>): <short description>

[optional body]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**
```
feat(ingestion): add YouTube comment fetcher
fix(streamlit): handle empty ABSA results gracefully
docs(api): update endpoint documentation
refactor(nlp): extract sentiment scoring to separate function
```

---

## Planning Workflow

All agents MUST use `agents_plans/` for work tracking:

1. **Before starting work:** Create a plan file in `agents_plans/task/`
2. **During work:** Move to `agents_plans/in_progress/`
3. **After completion:** Move to `agents_plans/dones/`

**Plan file format:**
```markdown
# <Title>

- **Owner:** <agent/contributor>
- **Status:** todo | in_progress | done
- **Module:** <affected module>

## Description
<what and why>

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

---

## Conventions & Patterns

### Data Contracts
- Define shared types in `libs/types/`
- Use consistent field names across modules:
  - `id` (UUID), `createdAt`, `updatedAt` (timestamps)
  - `source` (platform name), `externalId` (platform-specific ID)

### Idempotency
- All workers must be idempotent (safe to re-run)
- Use `(source, externalId)` for deduplication

### Error Handling
- Log errors with context (mention ID, job ID)
- Use structured logging (JSON format preferred)
- Implement retry with exponential backoff for transient failures

### API Patterns
- Use REST conventions (GET for reads, POST for creates)
- Support pagination via `page` and `limit` query params
- Return consistent error shapes: `{ error: string, code: string }`

---

## Quick Reference

| Task                        | Command/Location                              |
|-----------------------------|-----------------------------------------------|
| Run dashboard              | `cd frontend/web/streamlit && streamlit run streamlit_app.py` |
| Find module docs           | `<module>/README.md` and `<module>/AGENTS.md` |
| Create work plan           | Add to `agents_plans/task/`                   |
| Shared types               | `libs/types/`                                 |
| Domain entities            | `api/entities/`                               |
