# Web Crawl Ingestion Module

Tourism-focused web crawling engine using **Crawl4AI SDK v0.7.x** that automatically detects, extracts, and returns structured tourism content from web pages.

## Features

- **Intelligent Extraction**: Uses LLM-based extraction with Google Gemini
- **Content Type Routing**: Supports `forum`, `review`, `blog`, `agency`, and `auto` modes
- **Structured Output**: Returns clean JSON with reviews, comments, blog sections, and agency info
- **No Raw Markdown**: All content is extracted and structured text (not markdown)
- **Model Fallback Chain**: Automatically switches between models on rate limit errors

## Architecture

```
dto → core
dao → orm
examples → core + dto
```

### Module Structure

```
web-crawl/
├── dto/                    # Pydantic DTOs
│   ├── crawl_request_dto.py
│   └── crawl_result_dto.py
├── core/                   # Business logic
│   ├── extraction_router.py  # Strategy selection
│   ├── crawler.py           # Crawl4AI wrapper
│   └── crawl_service.py     # Main orchestrator
├── orm/                    # SQLAlchemy models
│   ├── base.py
│   ├── crawl_history_model.py
│   └── crawl_result_model.py
├── dao/                    # Data access
│   ├── crawl_history_dao.py
│   └── crawl_result_dao.py
├── examples/               # Usage examples
│   ├── run_console.py
│   └── requirements.txt
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Install Dependencies

```powershell
cd projects/services/ingestion/web-crawl
pip install -r requirements.txt
crawl4ai-setup
```

### 2. Set API Key

Create a `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run Example

```powershell
cd examples
python run_console.py
```

## Input Contract

```json
{
  "url": "string",
  "content_type": "forum" | "review" | "blog" | "agency" | "auto"
}
```

## Output Contract

```json
{
  "request_id": "string",
  "url": "string",
  "content_type": "string",
  "meta": {
    "crawl_time": "ISO-8601",
    "language": "string | null",
    "crawl_strategy": "single | deep",
    "extraction_strategy": "css | llm",
    "detected_sections": ["review", "comment", "information", "pricing"]
  },
  "content": {
    "title": "string | null",
    "information": "string | null",
    "reviews": [{"author": "string | null", "text": "string", "rating": "number | null"}],
    "comments": [{"author": "string | null", "text": "string"}],
    "blog_sections": [{"heading": "string", "text": "string"}],
    "agency_info": {"tour_name": "string | null", "price": "string | null", "duration": "string | null", "included_services": ["string"]}
  }
}
```

## Content Type Mapping

| content_type | Expected Sections |
|--------------|-------------------|
| forum | comments, travel experiences |
| review | reviews, ratings |
| blog | blog_sections, information |
| agency | agency_info, pricing |
| auto | all tourism-related sections |

## Usage in Code

```python
import asyncio
from dto import CrawlRequestDTO
from core import CrawlService

async def main():
    request = CrawlRequestDTO(
        url="https://example.com/travel-review",
        content_type="review"
    )
    
    service = CrawlService()
    result = await service.crawl(request)
    
    print(result.model_dump_json(indent=2))

asyncio.run(main())
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `WEBCRAWL_DATABASE_URL` | Database URL for persistence | No (defaults to SQLite) |

## Model Fallback Chain

The crawler uses a model fallback chain to handle rate limits. Models are tried in order:

1. `gemini/gemini-2.5-flash` - Default model
2. `gemini/gemini-2.5-flash-lite`
3. `gemini/gemma-3-27b`
4. `gemini/gemma-3-12b`

## Technology Stack

- **Crawl4AI**: Web crawling and LLM extraction
- **Pydantic**: Data validation and DTOs
- **SQLAlchemy**: ORM for persistence
- **LiteLLM**: LLM provider abstraction (Gemini)
