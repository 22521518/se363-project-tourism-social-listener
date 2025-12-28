# AGENTS.md

## 🎯 Agent Scope: Location Extraction Task

This agent is responsible for **extracting geographic locations from unified text events**, validating them, and preparing results for downstream systems. The agent operates **inside the processing service**, scoped strictly to the `location_extraction` task.

---

## 🧠 Core Responsibilities

- Consume `UnifiedTextEvent`
- Clean & normalize raw text
- Extract geographic locations (LLM / Rule-based)
- Persist extraction results to Postgres
- Publish completion events to Kafka
- Support human validation via UI

---

## 🧩 Agent Boundaries (Hard Rules)

- ❌ MUST NOT depend on ingestion-specific schemas

- ❌ MUST NOT call Kafka before persistence

- ❌ MUST NOT embed UI or Streamlit logic

- ❌ MUST NOT hardcode LLM providers

- ❌ MUST NOT implement Kafka retry or DLQ logic (handled by orchestrator)

- ✅ MUST accept canonical DTO only (`UnifiedTextEvent`)

- ✅ MUST return structured JSON

- ✅ MUST support extractor swapping

- ✅ MUST skip processing if record is marked `validated = true`

- ❌ MUST NOT publish Kafka events for skipped records

---

## 📦 Folder Scope (Task-level)

```
projects/services/processing/tasks/location_extraction/
├── cleaner/
├── normalizer/
├── pipeline/
├── nlp/
├── extractors/       <-- New: strategies (llm, gazetteer, regex)
├── validators/       <-- New: logic for confidence & schema checks
├── dto/
├── dao/
├── orm/
├── kafka/
├── ui_schema/
├── config/
```

The agent **owns everything inside this folder**, and nothing outside it.

---

## 🧠 Prompt Contract (LLM Location Extraction)

### SYSTEM PROMPT

```
You are a geographic information extraction system.
You must extract real-world geographic locations mentioned in the text.
Respond ONLY with valid JSON. Do not include explanations.
```

### USER PROMPT TEMPLATE

```json
{
  "task": "location_extraction",
  "instructions": [
    "Identify all geographic locations mentioned in the text",
    "Resolve aliases and abbreviations if possible",
    "If a location is ambiguous and cannot be resolved from context, mark type as 'unknown' and reduce confidence",
    "Choose one primary location if the intent is clear",
    "If no location exists, return empty arrays"
  ],
  "text": "{{INPUT_TEXT}}",
  "output_schema": {
    "locations": [
      {
        "name": "string",
        "type": "country|city|state|province|landmark|unknown",
        "confidence": "float"
      }
    ],
    "primary_location": {
      "name": "string",
      "confidence": "float"
    } | null,
    "overall_score": "float"
  }
}
```

### VALID RESPONSE EXAMPLE

```json
{
  "locations": [
    { "name": "Ho Chi Minh City", "type": "city", "confidence": 0.92 },
    { "name": "Vietnam", "type": "country", "confidence": 0.85 }
  ],
  "primary_location": {
    "name": "Ho Chi Minh City",
    "confidence": 0.92
  },
  "overall_score": 0.91
}
```

---

## 🔄 Fallback Strategy

If LLM fails:

1. Rule-based Gazetteer extractor
2. Regex-based country/city matcher
3. Return empty but valid schema

**Output Requirement**:
The final output must include metadata indicating which extractor was used:

```json
"meta": {
  "extractor": "llm|gazetteer|regex",
  "fallback_used": true
}
```

---

## 🧪 Validation Expectations

- Output must be valid JSON
- All confidence values ∈ [0,1]
- `primary_location` must exist in `locations` (check by name/reference)

---

## 🧑‍⚖️ Human-in-the-loop

Validation UI may:

- Edit locations
- Override primary location
- Mark record as validated

Agent must **never overwrite validated records**.

---

## 🚀 Implementation Status

### Implemented Components

| Component | Status | Description |
|-----------|--------|-------------|
| `config/` | ✅ Done | Configuration management with Pydantic Settings |
| `dto/` | ✅ Done | UnifiedTextEvent input and LocationExtractionResult output |
| `extractors/` | ✅ Done | LLM, Gazetteer, and Regex extractors |
| `validators/` | ✅ Done | Schema and confidence validation |
| `pipelines/` | ✅ Done | Extraction pipeline with fallback strategy |

### LLM Provider Support

The module supports **swappable LLM providers** via LangChain:

| Provider | Model | Free Tier |
|----------|-------|-----------|
| Google Gemini | `gemini-1.5-flash` | 60 QPM |
| TogetherAI | `meta-llama/Llama-3-70b-chat-hf` | Available |

### Quick Start

```python
from pipelines import extract_locations_from_text

# Simple text extraction
result = extract_locations_from_text("I visited Ho Chi Minh City last week")
print(result.to_dict())

# Using pipeline with custom event
from dto import UnifiedTextEvent
from pipelines import ExtractionPipeline

event = UnifiedTextEvent(
    source="youtube",
    source_type="comment",
    external_id="abc123",
    text="Beautiful sunset at Da Nang beach"
)

pipeline = ExtractionPipeline()
result = pipeline.process(event)
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
LLM_PROVIDER=google          # or 'togetherai'
GOOGLE_API_KEY=your_key_here
LLM_MODEL_NAME=gemini-1.5-flash
LLM_TEMPERATURE=0.1
```

### Dependencies

Install via: `pip install -r requirements.txt`

Key packages:
- `langchain`, `langchain-google-genai`, `langchain-together`
- `pydantic`, `pydantic-settings`
- `jsonschema`
