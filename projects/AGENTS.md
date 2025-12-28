# AGENTS.md – Step-by-Step Implementation Guide

> All planning artifacts, implementation plans, and task tracking go in `agents_plans/`.

---

## How to Work (Step-by-Step)

### Step 1: Plan First
1. Create a plan file in `agents_plans/tasks/<task-name>.md`
2. Define: goal, acceptance criteria, affected modules
3. Move to `agents_plans/in_progress/` when starting

### Step 2: Implement
1. Make minimal, focused changes
2. One logical unit per commit
3. Follow module-specific `AGENTS.md` for conventions

### Step 3: Verify
1. Run tests: `pytest tests/` (Python) or `npm test` (Node.js)
2. Verify manually if needed
3. Move plan to `agents_plans/dones/` when complete

---

## Artifacts Location

All artifacts go in `agents_plans/`:
- `tasks/` — new tasks
- `in_progress/` — active work
- `dones/` — completed work
- `epic/` — cross-module initiatives
- `module_or_features/` — feature plans by module

---

## Quick Commands

```powershell
# Streamlit Dashboard
cd frontend/web/streamlit && streamlit run streamlit_app.py

# Python Virtual Environment
python -m venv venv && .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt

# API (Node.js)
cd api && npm install && npm run dev

# Python Workers
cd services/<worker> && pip install -r requirements.txt && python main.py
```

---

## Code Style (Summary)

| Language | Style |
|----------|-------|
| Python | PEP 8, type hints, snake_case |
| TypeScript | ESLint, strict mode, camelCase |

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

## Commit Format

```
<type>(<scope>): <short description>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
## Commit Guidelines

### Commit Scope
- **Each commit should be minimal and scoped to a single function, module, or logic unit**
- Avoid large commits that span entire domains
- One logical change per commit

---

## Ignore Files

Use `.agentsignore` for exclusions.
