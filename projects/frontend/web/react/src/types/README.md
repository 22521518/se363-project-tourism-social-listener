# Frontend Types

TypeScript type definitions for the React frontend application.

## Files

### Core Types

| File | Description |
|------|-------------|
| `youtube_channel.ts` | YouTube channel data structure |
| `youtube_video.ts` | YouTube video data with metadata |
| `youtube_comment.ts` | YouTube comment with intention/traveling type |
| `intention.ts` | Intention classification types and colors |
| `traveling-type.ts` | Traveling type classification and colors |
| `location.ts` | Location extraction results from NER |

### Processing Types

| File | Description |
|------|-------------|
| `asca.ts` | ASCA (Aspect-based Sentiment Category Analysis) types |
| `web_crawl.ts` | Web crawl results (reviews, comments, blogs) |

## Usage

```typescript
import { YoutubeVideo } from '../types/youtube_video';
import { ASCAExtraction, CategoryType } from '../types/asca';
import { CrawlResult, ContentType } from '../types/web_crawl';
```

## Type Mapping to Backend

| Frontend Type | Backend DTO/Model |
|---------------|-------------------|
| `YoutubeChannel` | `ChannelDTO` (youtube) |
| `YoutubeVideo` | `VideoDTO` (youtube) |
| `YoutubeComment` | `CommentDTO` (youtube) |
| `IntentionStats` | `IntentionStatsDTO` (intention) |
| `TravelingTypeStats` | `TravelingStatsDTO` (traveling_type) |
| `Location` | `Location` (location_extraction) |
| `ASCAExtraction` | `ASCAExtractionResult` (asca) |
| `CrawlResult` | `CrawlResultDTO` (web-crawl) |
