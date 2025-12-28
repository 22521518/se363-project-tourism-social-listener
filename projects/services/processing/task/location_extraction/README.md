# README.md

## 📍 Location Extraction Processing Task

Production-ready processing task for extracting geographic locations from social content using **LLM + rules**, designed for **scalability, auditability, and human validation**.

---

## 🏗️ Architecture Overview

```
Ingestion (YouTube, FB, ...)
  ↓
UnifiedTextEvent (DTO)
  ↓
Location Extraction Pipeline
  ↓
Postgres (source of truth)
  ↓
Kafka (event notification)
  ↓
Streamlit UI (validate & audit)
```

Kafka is intentionally placed **after persistence**.

---

## 📂 Task-based Folder Structure

```
projects/services/processing/task/location_extraction/
├── cleaner/            # text cleaning
├── normalizer/         # language, unicode
├── pipeline/           # orchestration logic
├── nlp/
│   └── extractors/     # LLM / rule-based
├── dto/                # UnifiedTextEvent, Location DTO
├── dao/                # DB access only
├── orm/                # SQLAlchemy models
├── kafka/              # producer / consumer
├── ui_schema/          # validation schemas
├── config/             # llm, kafka, db
```

All modules are **grouped by task**, not by technical layer.

---

## 🔗 Canonical Input

All processing starts from:

```python
UnifiedTextEvent(
  source="youtube",
  source_type="comment",
  external_id="abc123",
  text="I moved to Da Nang last year",
  language=None,
  created_at=...,
  metadata={"video_id": "v1"}
)
```

No other input type is accepted.

---

## 🧠 Extractor Interface

```python
class LocationExtractor:
    def extract(self, text: str) -> dict:
        ...
```

You may plug in:

- LLM (LangChain)
- spaCy / Transformer model
- Rule-based system

---

## 🧾 Database Schema (Core Fields)

- raw_text (never modified)
- locations (JSON)
- primary_location
- score
- validated / validated_by

Validated records are immutable.

---

## 🖥️ Validation UI Schema

```json
{
  "id": "number",
  "raw_text": "string",
  "locations": [{ "name": "string", "type": "string", "confidence": "number" }],
  "primary_location": "string",
  "validated": "boolean",
  "validation_note": "string"
}
```

UI rules:

- Confidence editable
- Add/remove locations
- Save triggers DB update + Kafka event

---

## 🚫 Anti-patterns

- Calling LLM from UI
- Publishing Kafka before DB commit
- Overwriting validated records
- Mixing ingestion & processing schemas

---

## ✅ Design Guarantees

- Replaceable NLP models
- Human-in-the-loop ready
- Auditable history
- Safe for scale-out consumers

---

## 📌 Next Steps

- Add model-based extractor
- Train Geo-NER
- Add confidence calibration
- Analytics on correction rate

---

**Owner:** Processing / NLP Team

---

## 🚀 Quick Start Guide

### 1. Install Dependencies

```bash
cd projects/services/processing/task/location_extraction
pip install -r requirements.txt
```

### 2. Configure Environment (Optional for LLM)

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key (for LLM extraction)
# Get free Google Gemini key at: https://makersuite.google.com/app/apikey
```

### 3. Run Examples

```bash
# Test WITHOUT API key (uses Gazetteer/Regex fallback)
python examples/test_without_llm.py

# Test WITH LLM (requires API key in .env)
python examples/test_with_llm.py

# Full examples
python examples/basic_usage.py
```

---

## 💻 Usage Examples

### Simple Text Extraction

```python
from pipelines import extract_locations_from_text

result = extract_locations_from_text("I visited Da Nang last week")

print(result.locations)        # List of Location objects
print(result.primary_location) # Primary location or None
print(result.overall_score)    # Confidence score 0-1
print(result.meta.extractor)   # 'llm', 'gazetteer', or 'regex'
```

### Pipeline with Event

```python
from dto import UnifiedTextEvent
from pipelines import ExtractionPipeline

event = UnifiedTextEvent(
    source="youtube",
    source_type="comment",
    external_id="abc123",
    text="Beautiful beaches in Nha Trang!",
    language="en",
    metadata={"video_id": "xyz"}
)

pipeline = ExtractionPipeline()
result = pipeline.process(event)

# Convert to dict for JSON/database
data = result.to_dict()
```

### Without LLM (No API Key Needed)

```python
from extractors import GazetteerLocationExtractor, RegexLocationExtractor
from pipelines import ExtractionPipeline

pipeline = ExtractionPipeline(
    llm_extractor=None,  # Disable LLM
    gazetteer_extractor=GazetteerLocationExtractor(),
    regex_extractor=RegexLocationExtractor()
)

result = pipeline.process(event)
```

---

## 🔧 Integration Patterns

### In Airflow DAG

```python
import sys
sys.path.append('/path/to/location_extraction')

from dto import UnifiedTextEvent
from pipelines import ExtractionPipeline

def extract_locations_task(**context):
    text = context['ti'].xcom_pull(task_ids='fetch_data')
    
    event = UnifiedTextEvent(
        source="airflow",
        source_type="pipeline",
        external_id=context['run_id'],
        text=text
    )
    
    pipeline = ExtractionPipeline()
    result = pipeline.process(event)
    
    context['ti'].xcom_push(key='locations', value=result.to_dict())
```

### In FastAPI

```python
from fastapi import FastAPI

import sys
sys.path.append('/path/to/location_extraction')

from dto import UnifiedTextEvent
from pipelines import ExtractionPipeline

app = FastAPI()
pipeline = ExtractionPipeline()

@app.post("/extract")
def extract_locations(text: str):
    event = UnifiedTextEvent(
        source="api",
        source_type="request",
        external_id="api",
        text=text
    )
    return pipeline.process(event).to_dict()
```

---

## 📤 Output Format

```json
{
  "locations": [
    {"name": "Ho Chi Minh City", "type": "city", "confidence": 0.92},
    {"name": "Vietnam", "type": "country", "confidence": 0.85}
  ],
  "primary_location": {
    "name": "Ho Chi Minh City",
    "confidence": 0.92
  },
  "overall_score": 0.88,
  "meta": {
    "extractor": "llm",
    "fallback_used": false
  }
}
```

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| `No module named 'langchain'` | Run `pip install -r requirements.txt` |
| `GOOGLE_API_KEY is required` | Set API key in `.env` or use `llm_extractor=None` |
| Empty results | Use LLM extractor for best results, or check if text contains recognized locations |

