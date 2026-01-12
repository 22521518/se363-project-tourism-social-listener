# API Services

Business logic layer that processes data from repositories.

## Files

### YouTube Services
| File | Description |
|------|-------------|
| `youtube_channel.service.ts` | Channel business logic |
| `youtube_video.service.ts` | Video processing and filtering |
| `youtube_comment.service.ts` | Comment aggregation |

### Processing Services
| File | Description |
|------|-------------|
| `intention.service.ts` | Intention stats aggregation with colors |
| `traveling_type.service.ts` | Traveling type stats with colors |
| `location.service.ts` | Geography stats (Domestic/Regional/International) |
| `asca.service.ts` | ASCA category stats formatting |
| `crawl.service.ts` | Web crawl results with pagination |

## Service Pattern

Services:
1. Call repositories for raw data
2. Transform/aggregate data for API responses
3. Add presentation data (colors, labels)
4. Handle errors gracefully

### Example: ASCA Service

```typescript
import { ascaRepository } from "../repositories/asca.repository";

const CATEGORY_COLORS: Record<CategoryType, string> = {
  LOCATION: '#3b82f6',
  PRICE: '#10b981',
  // ...
};

export class ASCAService {
  async getStats(): Promise<ASCAStatsFormatted[]> {
    try {
      const stats = await ascaRepository.getCategoryStats();
      return this.formatStats(stats);
    } catch (error) {
      // Graceful fallback when tables don't exist
      console.warn('ASCA tables may not exist:', error);
      return this.formatStats([]);
    }
  }

  private formatStats(stats: ASCACategoryStats[]): ASCAStatsFormatted[] {
    // Ensure all categories present, add colors, sort by total
    return allCategories.map(category => ({
      category,
      positive: stat?.positive || 0,
      negative: stat?.negative || 0,
      neutral: stat?.neutral || 0,
      total: stat?.total || 0,
      color: CATEGORY_COLORS[category],
    })).sort((a, b) => b.total - a.total);
  }
}

export const ascaService = new ASCAService();
```

## Error Handling

Services implement graceful degradation:
- Return empty/default data when tables don't exist
- Log warnings for debugging
- Never throw to controllers (catch all)

## Response Formatting

Services format data for frontend consumption:
- Add color codes for visualization
- Compute percentages and aggregates
- Sort by relevance (total, count, etc.)
- Include all categories even with 0 values
