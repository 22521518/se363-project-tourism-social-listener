# API Repositories

Data access layer for database operations using raw SQL queries.

## Files

### YouTube Repositories
| File | Description |
|------|-------------|
| `youtube_channel.repository.ts` | CRUD for YouTube channels |
| `youtube_video.repository.ts` | Queries for videos with pagination |
| `youtube_comment.repository.ts` | Comment queries with joins |

### Processing Repositories
| File | Description |
|------|-------------|
| `intention.repository.ts` | Intention data queries |
| `traveling_type.repository.ts` | Traveling type queries |
| `location.repository.ts` | Location extraction queries |
| `asca.repository.ts` | ASCA aspect-sentiment queries |
| `crawl.repository.ts` | Web crawl result queries |

## Repository Pattern

Each repository:
1. Uses the shared `query` function from `database/connection.ts`
2. Defines raw interfaces for database rows
3. Implements mapping functions to convert rows to entities
4. Exports a singleton instance

### Example: ASCA Repository

```typescript
import { query } from "../database/connection";
import { ASCACategoryStats } from "../entities/asca.entity";

export class ASCARepository {
  // Get aggregated stats by category using JSONB unnesting
  async getCategoryStats(): Promise<ASCACategoryStats[]> {
    const sql = `
      SELECT 
        aspect->>'category' as category,
        aspect->>'sentiment' as sentiment,
        COUNT(*) as count
      FROM asca_extractions,
           jsonb_array_elements(aspects) as aspect
      WHERE is_deleted = false
      GROUP BY aspect->>'category', aspect->>'sentiment'
    `;
    // ...
  }
}

export const ascaRepository = new ASCARepository();
```

## Database Connection

All repositories use the shared connection pool:

```typescript
import { query } from "../database/connection";

// Simple query
const result = await query<RowType>(sql);

// Parameterized query
const result = await query<RowType>(sql, [param1, param2]);
```

## Error Handling

Repositories throw errors on failure. Services should catch and handle:
- Missing tables (graceful fallback)
- Connection errors
- Query errors
