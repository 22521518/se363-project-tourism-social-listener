# API Controllers

HTTP route handlers that expose API endpoints.

## Files

### YouTube Controllers
| File | Base Route | Description |
|------|------------|-------------|
| `youtube_channel.controller.ts` | `/api/youtube_channels` | Channel endpoints |
| `youtube_video.controller.ts` | `/api/youtube_videos` | Video endpoints |
| `youtube_comment.controller.ts` | `/api/youtube_comments` | Comment endpoints |

### Processing Controllers
| File | Base Route | Description |
|------|------------|-------------|
| `intention.controller.ts` | `/api/intentions` | Intention stats |
| `traveling_type.controller.ts` | `/api/traveling_types` | Traveling type stats |
| `location.controller.ts` | `/api/locations` | Location geography |
| `asca.controller.ts` | `/api/asca` | ASCA aspect sentiment |
| `crawl.controller.ts` | `/api/crawl_results` | Web crawl results |

## API Endpoints

### ASCA Endpoints
```
GET /api/asca/stats              → All category stats
GET /api/asca/stats/video/:id    → Stats for specific video
GET /api/asca/counts             → Total/approved/pending counts
```

### Web Crawl Endpoints
```
GET /api/crawl_results                        → Paginated results
GET /api/crawl_results?content_type=review    → Filter by type
GET /api/crawl_results?limit=20&offset=0      → Pagination
GET /api/crawl_results/stats                  → Stats by content type
```

### Intention Endpoints
```
GET /api/intentions/stats              → All intention stats
GET /api/intentions/stats/video/:id    → Stats for specific video
```

### Location Endpoints
```
GET /api/locations/geography    → Geography stats (Domestic/Regional/International)
```

## Response Format

All endpoints return consistent JSON:

```json
{
  "success": true,
  "data": [ ... ]
}
```

For paginated endpoints:
```json
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "hasMore": true
  }
}
```

## Error Handling

```typescript
try {
  const data = await service.getData();
  res.json({ success: true, data });
} catch (error) {
  console.error('Error:', error);
  res.status(500).json({ success: false, error: 'Failed to fetch data' });
}
```

## OpenAPI/Swagger

Controllers include JSDoc comments for Swagger documentation:

```typescript
/**
 * @openapi
 * /api/asca/stats:
 *   get:
 *     summary: Get ASCA category statistics
 *     tags: [ASCA]
 *     responses:
 *       200:
 *         description: Successfully retrieved stats
 */
```

Access Swagger UI at: `http://localhost:3001/api-docs`
