# Agents Architecture and Specification

This document defines agent-oriented architecture for the Social Listener for Tourism project. It is organized into four abstraction layers: Repository, Domain, Component, and Entity. It also includes recommendations for restructuring the repository into a domain-driven monorepo so agents, services and the frontend have clear boundaries and a shared contract.

---

## 1. Repository Level

### Global architecture (recommended monorepo)

- This repo should be converted into a small monorepo containing `frontend/` and `services/` packages. Agents and services are developed and deployed independently but share a common types package and an OpenAPI contract.
- Runtime topology (recommended):
  - Frontend: Vite-built SPA (served by CDN or static host) in `frontend/`.
  - API service: `services/api/` — exposes REST/GraphQL endpoints for mentions, aggregates, metadata.
  - Ingestion worker(s): `services/ingestion/` — collects raw posts, writes to queue or DB.
  - NLP/enrichment worker(s): `services/nlp/` — performs language detection, sentiment, topic extraction and embeddings.
  - Aggregator workers: `services/aggregator/` — compute materialized metrics and caches.
  - Orchestrator: workflow engine (Airflow/Prefect) or lightweight scheduler (cron/Fargate scheduled tasks) for backfills and scheduled aggregations.
  - Infrastructure: Postgres, OpenSearch/Elasticsearch, Redis, S3 (optional) for media.

### Subsystems and agent interactions

- Ingestion subsystem: agents in `services/ingestion/` collect raw posts and write to an event queue (Kafka/Redis Streams/SQS). Provide a simple local runner and a staging runner for testing.
- Enrichment/NLP subsystem: agents in `services/nlp/` read raw events, enrich them (language, sentiment, entities, topics, embeddings), then write enriched mentions to the primary datastore and index.
- Aggregation subsystem: `services/aggregator/` computes time-windowed metrics and materialized views for the frontend; expose these via the API service.
- Notification/Alert subsystem: a lightweight rule worker consumes aggregates or streams and pushes notifications (webhooks, email, Slack).
- Admin/Metadata subsystem: a sync worker maintains lookup tables (regions, orgs, taxonomy) and publishes them to the API or CDN.

Notes:

- Start with simple transport (HTTP + Postgres + OpenSearch) for early development; add message queues when throughput grows.
- Use OpenAPI as the contract between `frontend/` and `services/api/`; generate clients from the spec and keep types in `libs/types`.

---

## 2. Domain Level

This section maps core domains to agent responsibilities and expectations.

### Ingestion

- Purpose: Collect public social posts (or stream from partners) and persist raw messages.
- Boundaries: Responsible only for collecting and initial normalization (timestamps, minimal parsing). No heavy enrichment.
- Agent roles:
  - Platform connectors (Twitter/X, Instagram, Facebook, TikTok, RSS, partner APIs).
  - Queue writers (publish raw messages to Kafka/SQS).
- Data contracts:
  - RawMessage: { source, externalId, rawText, createdAt, author, rawPayload }

### NLP / Enrichment

- Purpose: Add semantic layers: language detection, sentiment, topics, classification (tourism purpose), named entities, geo extraction, embeddings.
- Boundaries: Idempotent enrichment; workers should be idempotent and safe to re-run on a mention.
- Agent roles:
  - Sentiment worker: produces { sentiment: positive|neutral|negative, score }
  - Topic/semantic worker: produces topic tags, embeddings
  - Classification worker: tourism purpose, post type
- Data contracts:
  - EnrichedMention: extends RawMessage with { sentiment, topics, classifications, entities, embeddings }

Implementation notes:

- Prefer Python for advanced NLP (spaCy, transformers) and model serving (FastAPI) when heavy ML is required.
- Provide a thin Node-based enrichment stub for early integration tests (returns deterministic outputs for sample inputs).

### Analytics / Aggregation

- Purpose: Create aggregated metrics and materialized views for the dashboard (counts, time series, distribution by sentiment, geographies, topics).
- Boundaries: Batch and near real-time aggregates; provide time-windowed endpoints for charts.
- Agent roles:
  - Aggregator: computes stats and stores results in an aggregates table or cache
  - Trend detector: identifies rising topics and surfaces them via API

### Alerts / Notifications

- Purpose: Monitor conditions and emit alerts when thresholds or patterns are matched.
- Agent roles:
  - Rule engine worker: evaluates alert rules against aggregates or streaming data
  - Dispatcher: sends notifications (webhooks, email, Slack)

### Admin / Metadata

- Purpose: Manage reference data (tourism purposes, org lists, geographies) used by filters and UI
- Agent roles:
  - Metadata sync worker: periodically refresh lookups and push them to API or CDN

---

## 3. Component Level

Below are the major UI components and how agents and APIs typically integrate with them. This section focuses on responsibilities, inputs/outputs and integration points from the agent perspective.

### `AdvancedFilters`

- Responsibilities: Hold and edit global filter state (time range, sentiment, geo, org, tourismPurpose, postType).
- Inputs: UI interactions; initial filter options (lists) from API `/api/metadata`.
- Outputs: Emits filter change events used to fetch filtered data for other components.
- Integration: Agents that update metadata (e.g., org list) should write to the metadata API consumed by this component.
- Error handling: Show friendly messages if metadata cannot be loaded; allow local fallback options.

Front-end convention:

- Move feature components under `frontend/src/domains/<domain>/components` so each domain owns its UI and tests. Shared primitives remain in `frontend/src/components/ui`.

### `QuickStats`

- Responsibilities: Display top-level KPIs (total mentions, positive/negative counts, top topics).
- Inputs: Aggregates API `/api/aggregates/overview?filters...` (counts, percentages).
- Outputs: None (read-only display).
- Integration: Aggregator agents compute and store the aggregates endpoint used here. Should tolerate partial data and show stale indicators.

### `TourismClassification` & `PostTypeAnalysis`

- Responsibilities: Visualize classification distributions (tourism purposes, post types).
- Inputs: `/api/aggregates/classification?filters...` returning category breakdowns.
- Decision logic: Visualize top categories, collapse small buckets into "other".
- Error handling: If API fails, show cached data or a retry option.

### `SemanticAnalysis` & `SentimentChart`

- Responsibilities: Show topic clusters, sentiment over time and semantic summaries.
- Inputs: `/api/semantic/topics`, `/api/metrics/sentiment`.
- Integration: Semantic and sentiment workers produce the inputs. Charts should render gracefully when embedding vectors are used (server-side clustering preferred).

### `DetailedMentions`

- Responsibilities: Paginated list of mentions, search and detail view.
- Inputs: `/api/mentions?filters...&page=...` (mentions with enriched fields).
- Outputs: Trigger detail inspection; may request additional context from `/api/mentions/{id}/context`.
- Integration: Search index (OpenSearch) is the recommended backing store for fast queries and free-text search.
- Error handling: If mention fetch fails, show per-item fallback; if page fails, allow retry/pagination fallback.

Indexing guidance:

- Enrichment workers should write enriched mentions to the primary DB and also push to the search index. Keep indexing idempotent and include a `version` or `updatedAt` field.

### `ItineraryTracker`

- Responsibilities: Track posts tied to a named itinerary or trip, visualize journey and touchpoints.
- Inputs: itinerary membership API `/api/itineraries/{id}/mentions` and metadata for locations.
- Integration: Agents tag mentions with itinerary IDs (either manual or via heuristics) and write relationships to DB.

Implementation note:

- Provide simple endpoints for CRUD of itineraries in `services/api` and allow `ingestion` or `nlp` workers to attach mentions to itineraries by heuristics (geofence, date ranges, hashtags).

### Shared integration patterns

- All components should call stable API endpoints with a clear filter contract. Prefer a single `filters` object serialized as query parameters or request body.
- Error handling: components should show skeletons/placeholders, then a human-friendly error banner if data cannot be retrieved. Use toasts (e.g., `sonner`) for transient errors.

---

## 4. Entity Level

This section describes important domain entities, attributes and lifecycle events. Agents will create, read, update and enrich these entities.

### `Mention` (core entity)

- Attributes (recommended):

  - `id` (UUID)
  - `source` (string) — platform
  - `externalId` (string) — platform-specific id
  - `text` (string)
  - `author` ({ id, handle, displayName })
  - `createdAt` (timestamp)
  - `ingestedAt` (timestamp)
  - `language` (string)
  - `sentiment` ({ label, score })
  - `topics` (array of strings)
  - `embeddings` (vector) — optional, for semantic search
  - `postType` (enum)
  - `tourismPurpose` (enum)
  - `geo` ({ lat, lon, country, region })
  - `media` (array of URLs/objects)
  - `rawPayload` (JSON)

- Relationships:

  - Belongs to zero-or-more `Itinerary`
  - Associated with zero-or-more `Topic` entities

- Lifecycle events:
  - Ingested: created by ingestion agent (RawMessage)
  - Enriched: NLP agents add sentiment/topics/embeddings (EnrichedMention)
  - Indexed: search index updated for fast querying
  - Aggregated: metrics workers include mention in aggregates

Storage guidance:

- Keep canonical mentions in Postgres and push denormalized copies to OpenSearch for search. Store embeddings separately (vector DB or a dedicated field) depending on scale.

### `AggregatedMetrics`

- Attributes: metric name, time window (start, end), group-by fields (e.g., sentiment, topic), value (count/score)
- Lifecycle: generated by aggregator agents on schedule or in near-real-time and stored in a cache or materialized view.

### `Itinerary`

- Attributes: id, name, start/end date, associated geo-points, owner, status
- Lifecycle: created by administrators or inferred automatically; agents attach mentions to itineraries through heuristics or manual tagging.

### `Topic` / `Entity`

- Attributes: id, label, canonicalForm, parentTopic (optional), sampleMentions
- Lifecycle: discovered by topic modeling agents or maintained by human curators; used for tagging and aggregations.

---

## Operational recommendations for agents

- Idempotency: Agents should process messages idempotently (use deduplication via `externalId` and `source`).
- Observability: Emit metrics (counts, latencies, errors) and structured logs (mention id, job id). Provide traces for long-running enrichments.
- Backpressure & retries: Agents writing to downstream stores should implement exponential backoff and dead-letter queues for poison records.
- Security: Sanitize any external content and follow rate limits for social platforms. Protect API keys with a secrets manager.

---

## Example API suggestions (for the frontend to consume)

- GET `/api/metadata` — returns lists for filters (regions, orgs, tourism purposes, post types)
- GET `/api/mentions?filters...&page=` — paginated enriched mentions
- GET `/api/aggregates/overview?filters...` — top-level KPIs
- GET `/api/semantic/topics?filters...` — topics and cluster summaries
- GET `/api/itineraries` and `/api/itineraries/{id}/mentions`

These endpoints should return JSON with stable schemas and support `filters` (timeRange, sentiment, geo, tourismPurpose, postType, org)

---

### Practical developer patterns and templates

- OpenAPI-first: keep an `openapi.yaml` in `services/api/` and generate TypeScript clients into `libs/types` to avoid drift.
- Worker templates: provide small example templates (one-liners) in `services/ingestion`, `services/nlp`, and `services/aggregator` that read test messages and output enriched examples.
- Local dev: `docker-compose.yml` should bring up `frontend`, `services/api` (mock), `postgres`, `opensearch`, and `redis` for integration testing.

---

If you'd like, I can: generate an OpenAPI spec for these endpoints, scaffold a minimal Node/Express API that exposes these routes (with mocked data), or create worker templates (ingestion/NLP/aggregator) for your preferred platform (Airflow, Prefect, serverless). Tell me which you'd prefer next.
