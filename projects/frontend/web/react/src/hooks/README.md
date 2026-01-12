# Frontend Hooks

Custom React hooks for data fetching and state management.

## Available Hooks

### YouTube Data

| Hook | Description | API Endpoint |
|------|-------------|--------------|
| `useYoutubeChannelData` | Fetch YouTube channels | `/api/youtube_channels` |
| `useYoutubeVideoData` | Fetch videos with pagination | `/api/youtube_videos` |
| `useYoutubeVideoDetailData` | Fetch single video details | `/api/youtube_videos/:id` |
| `useYoutubeCommentData` | Fetch comments for a video | `/api/youtube_comments` |

### Processing Data

| Hook | Description | API Endpoint |
|------|-------------|--------------|
| `useIntentionData` | Fetch intention statistics | `/api/intentions/stats` |
| `useTravelingTypeData` | Fetch traveling type stats | `/api/traveling_types/stats` |
| `useGeographyData` | Fetch location geography stats | `/api/locations/geography` |
| `useASCAData` | Fetch ASCA aspect sentiment stats | `/api/asca/stats` |
| `useWebCrawlData` | Fetch web crawl results | `/api/crawl_results` |

## Usage Examples

### Basic Usage

```typescript
import { useYoutubeVideoData } from '../hooks/useYoutubeVideoData';

function MyComponent() {
  const { data, meta, loading, error, refetch, fetchMore } = useYoutubeVideoData();
  
  if (loading) return <Spinner />;
  if (error) return <Error message={error} />;
  
  return (
    <div>
      {data.map(video => <VideoCard key={video.id} video={video} />)}
      {meta.hasMore && <button onClick={fetchMore}>Load More</button>}
    </div>
  );
}
```

### With Filters

```typescript
import { useASCAData } from '../hooks/useASCAData';

function VideoAnalysis({ videoId }: { videoId: string }) {
  // Pass videoId to filter stats for specific video
  const { data, loading } = useASCAData(videoId);
  
  return <ASCAAnalysis data={data} />;
}
```

## Hook Return Types

All hooks return a consistent interface:

```typescript
interface UseDataResult<T> {
  data: T[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

// For paginated hooks
interface UsePaginatedDataResult<T> extends UseDataResult<T> {
  meta: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
  fetchMore: () => void;
}
```
