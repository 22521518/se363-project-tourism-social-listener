# AGENTS.md - YouTube Ingestion Service

## Module Goal
Ingest channel, video, and comment data from YouTube Data API v3, persist to PostgreSQL, and emit events to Kafka.

## Core Capabilities
- **Channel Ingestion**: By ID (`UC...`) or Handle (`@...`).
- **Video Ingestion**: Recent videos, details, statistics.
- **Comment Ingestion**: Top-level comments and replies.
- **Tracking**: Periodic polling for new content.

## Key Files
- `api_manager.py`: YouTube API interaction. Handles quota management and handle-to-ID resolution.
- `tracking_manager.py`: Logic for monitoring channels.
- `dao.py`: Database access.
- `kafka_producer.py`: Event emission.

## Development Guidelines

### Handle Resolution
- Always use `api_manager.resolve_handle_to_id(handle)` when accepting user input that might be a handle.
- The system tries `forHandle` (1 unit) first, then falls back to `search` (100 units).

### Quota Management
- Be mindful of method costs.
- `search().list`: 100 units (Expensive)
- `channels().list`: 1 unit (Cheap)
- Default quota is 10,000 units/day.

### Testing
```powershell
# Run unit tests
pytest tests/

# Run verification script (requires valid .env)
python -m youtube.tests.verify_handle
```

### Common Commands
```powershell
# Run standalone ingestion for a channel
python -m youtube.main --mode=full --channel=@KhoaiLangThang
```
