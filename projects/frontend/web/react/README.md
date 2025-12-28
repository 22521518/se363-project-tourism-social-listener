# Social Listener for Tourism

This repository contains the frontend of the Social Listener for Tourism product and a set of recommended architectural and workflow changes to make development, testing and extension easier.

This update recommends converting the project to a small monorepo and adopting a domain-driven structure that separates frontend UI concerns from backend services and data-processing agents. The goal is to make development environments reproducible, to encourage clear API contracts, and to simplify adding ingestion/NLP/aggregator workers in languages and runtimes appropriate for each responsibility.

---

## Summary of recommended restructure

- Convert to a workspace/monorepo layout (npm workspaces, pnpm, or yarn workspaces) containing at least:
  - `frontend/` — the Vite + React SPA (current code moves here)
  - `services/api/` — minimal Node/Express or Fastify API that exposes endpoints consumed by the frontend (can start as mocked responses)
  - `services/ingestion/` — ingestion workers (Python/Node) for connecting to social platforms
  - `services/nlp/` — NLP/enrichment workers (Python preferred for ML libraries) or serverless functions
  - `services/aggregator/` — aggregation and metrics workers
  - `libs/` — shared TypeScript types, OpenAPI client, and utility code
  - `docs/` — longer-running architecture and runbooks (this file can live there)

This split keeps domain code focused, encourages independent lifecycle and scaling of agents, and makes local development simpler via docker-compose or workspace scripts.

## Goals of the restructure

- Domain separation: group UI, API, ingestion, enrichment and aggregation code by purpose.
- Clear contracts: rely on an OpenAPI (or JSON Schema) spec as the single source of truth for data contracts between frontend and services.
- Local dev parity: provide a single `dev` script to bring up the frontend and minimal mock API backend (via `docker-compose` or workspace scripts).
- Testability: add unit tests to frontend and service packages, and integration tests hitting the local mock API.

---

## Proposed new repository layout

```
.
├─ package.json                 # workspace root (scripts, workspace config)
├─ README.md
├─ agents.md
├─ libs/
│  └─ types/                    # shared TS types, DTOs
├─ frontend/
│  ├─ package.json
│  ├─ vite.config.ts
│  ├─ src/
│  │  ├─ domains/               # domain-based feature folders (mentions, analytics, itinerary)
│  │  │  ├─ mentions/
│  │  │  │  ├─ components/
│  │  │  │  ├─ hooks/
│  │  │  │  └─ types.ts
│  │  │  └─ analytics/
│  │  ├─ components/ui/         # primitives
│  │  ├─ services/              # API client wrappers and mocks
│  │  └─ types/                 # local type aliases (import shared from `libs/types`)
│  └─ ...
├─ services/
│  ├─ api/                      # minimal API (OpenAPI-first) with mocked responses
│  ├─ ingestion/                # platform connectors and queue writers
│  ├─ nlp/                      # enrichment workers (sentiment, topics, embeddings)
│  └─ aggregator/               # computes aggregates and exposes materialized endpoints
├─ docker-compose.yml           # local dev orchestration for API + frontend + storage (Postgres/Redis/Elasticsearch)
└─ docs/
   └─ runbooks/
```

---

## Migration checklist (minimal steps to move to the new layout)

1. Create workspace root `package.json` and move current `package.json` into `frontend/package.json`.
2. Move all existing `src/` and frontend assets into `frontend/src/` and update `main.tsx` imports if required.
3. Add `libs/types` package with the core DTOs: `Mention`, `AggregatedMetrics`, `Itinerary` (copy types into a single source-of-truth).
4. Scaffold `services/api/` with an OpenAPI spec and a small mock server that returns the shapes required by the frontend. Use `openapi-generator` or `express` + `swagger-ui`.
5. Add a `dev` script at repo root that boots the mock API and the frontend concurrently (or provide `docker-compose` to run both).
6. Create example worker templates (`ingestion`, `nlp`, `aggregator`) with README and a simple runner that reads/writes test messages (e.g., to a Redis stream or local file) so contributors can prototype.
7. Add CI pipeline to build and lint each package; add tests for critical types, API contract, and a smoke test that the frontend can fetch from the mock API.

---

## Developer onboarding (short)

1. Install Node.js and Docker.
2. From repo root:

```powershell
npm install
npm run dev            # will run workspace dev script (start mock API + frontend)
```

3. Run unit tests for a package:

```powershell
cd frontend
npm test
```

## Recommended tools & tech choices

- Monorepo tooling: `pnpm` workspaces (recommended) or npm workspaces.
- Mock server / API: OpenAPI + `express`/`fastify` or `json-server` for quick mocks.
- Workers: Python (for NLP) and Node (for lightweight orchestrators) depending on library needs.
- Search & indices: OpenSearch/Elasticsearch for text search; Postgres for relational storage; Redis for queues/cache.
- Local orchestration: `docker-compose` with services: `frontend`, `api`, `postgres`, `opensearch`, `redis`.

---

## Example developer commands (root workspace)

Start everything (mock API + frontend) for local dev:

```powershell
# from repo root (after setting up workspaces)
npm run dev
```

Build frontend only:

```powershell
cd frontend
npm run build
```

---

## Next steps I can help with

- Scaffold the workspace `package.json` and move frontend into `frontend/`.
- Create a minimal `services/api/` mock server with OpenAPI and a generated TypeScript client in `libs/`.
- Add `docker-compose.yml` to orchestrate local dev dependencies (Postgres, Redis, OpenSearch).

If you want, I can implement any of the above steps directly in the repo — tell me which to start with.
