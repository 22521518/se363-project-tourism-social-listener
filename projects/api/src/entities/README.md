# API Entities

TypeScript entity definitions that map to database models.

## Files

### YouTube Entities
| File | Table | Description |
|------|-------|-------------|
| `youtube_channel.entity.ts` | `youtube_channels` | YouTube channel data |
| `youtube_video.entity.ts` | `youtube_videos` | YouTube video metadata |
| `youtube_comment.entity.ts` | `youtube_comments` | YouTube comments |

### Processing Entities
| File | Table | Description |
|------|-------|-------------|
| `intention.entity.ts` | `intentions` | User intention classifications |
| `traveling_type.entity.ts` | `traveling_types` | Travel type classifications |
| `location.entity.ts` | `location_extractions` | NER location extractions |
| `asca.entity.ts` | `asca_extractions` | Aspect-based sentiment analysis |
| `crawl.entity.ts` | `crawl_result`, `crawl_history` | Web crawl results |

## Entity Structure

Each entity file typically includes:
- Type definitions (enums, interfaces)
- Main entity interface
- Response/Stats interfaces for API output

### Example: ASCA Entity

```typescript
// Enums
export type CategoryType = 'LOCATION' | 'PRICE' | 'ACCOMMODATION' | 'FOOD' | 'SERVICE' | 'AMBIENCE';
export type SentimentType = 'positive' | 'negative' | 'neutral';

// Main entity
export interface ASCAExtraction {
  id: string;
  source_id: string;
  source_type: string;
  aspects: AspectSentiment[];
  // ...
}

// Stats response
export interface ASCACategoryStats {
  category: CategoryType;
  positive: number;
  negative: number;
  neutral: number;
  total: number;
}
```

## Mapping to Python Models

| API Entity | Python ORM Model | Location |
|------------|------------------|----------|
| `ASCAExtraction` | `ASCAExtractionModel` | `services/processing/tasks/asca/orm/models.py` |
| `CrawlResult` | `CrawlResult` | `services/ingestion/web-crawl/orm/crawl_result_model.py` |
| `IntentionExtraction` | `IntentionModel` | `services/processing/tasks/intention/models.py` |
