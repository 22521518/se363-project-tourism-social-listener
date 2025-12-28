# YouTube Ingestion Module

YouTube Data API v3 connector for the Social Listening Tool. Collects channel metadata, videos, and comments for downstream sentiment analysis.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    YouTube Ingestion Module                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │ API Manager  │───▶│ Tracking Manager │───▶│ Kafka Producer│  │
│  └──────────────┘    └──────────────────┘    └───────────────┘  │
│         │                    │                       │           │
│         ▼                    ▼                       ▼           │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │  YouTube API │    │    PostgreSQL    │    │     Kafka     │  │
│  └──────────────┘    └──────────────────┘    └───────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

| Component        | File                  | Purpose                                 |
| ---------------- | --------------------- | --------------------------------------- |
| API Manager      | `api_manager.py`      | YouTube API wrapper with retry logic    |
| Tracking Manager | `tracking_manager.py` | Channel monitoring, new video detection |
| Kafka Producer   | `kafka_producer.py`   | Event publishing to Kafka               |
| Kafka Consumer   | `kafka_consumer.py`   | Event consumption and processing        |
| DAO              | `dao.py`              | Database operations                     |
| ORM Models       | `models.py`           | SQLAlchemy models                       |
| DTOs             | `dto.py`              | Data transfer objects                   |

## Code Style (Summary)

- Python: PEP 8, type hints, snake_case, python 3.12

## Quick Start

### 1. Install Dependencies

```powershell
cd projects/services/ingestion/youtube
pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
# Copy example env file
cp .env.example .env

# Edit .env with your settings
# Required: YOUTUBE_API_KEY
```

### 3. Initialize Database & Kafka

```powershell
python -m youtube.main --mode=init-db
python -m youtube.main --mode=init-kafka
```

### 4. Run Ingestion

```powershell
# Full ingestion for a channel
python -m youtube.main --mode=full --channel=UC_x5XG1OV2P6uZZ5FSM9Ttw

# Real-time tracking (continuous polling)
python -m youtube.main --mode=realtime --interval=60

# Scheduled tracking (APScheduler)
python -m youtube.main --mode=scheduled --interval=5
```

## API Manager

Encapsulates all YouTube Data API v3 operations.

### Channel Operations

```python
from youtube.api_manager import YouTubeAPIManager
from youtube.config import IngestionConfig

config = IngestionConfig.from_env()
api = YouTubeAPIManager(config)

# Fetch channel info (Supports ID or Handle)
channel = await api.fetch_channel_info("UC_x5XG1OV2P6uZZ5FSM9Ttw")
# OR
channel = await api.fetch_channel_info("@KhoaiLangThang")

# Populate channel to database
channel = await api.populate_channel("@KhoaiLangThang")
```

### Video Operations

```python
# Fetch channel videos
videos = await api.fetch_channel_videos("UC_x5XG1OV2P6uZZ5FSM9Ttw", max_results=50)

# Fetch single video
video = await api.fetch_video_details("dQw4w9WgXcQ")
```

### Comment Operations

```python
# Fetch video comments
comments = await api.fetch_video_comments("dQw4w9WgXcQ", max_results=100)
```

## Tracking Workflow

1. **Register Channel**: Add channel to tracking list
2. **Poll for Updates**: Check for new videos at intervals
3. **Detect New Videos**: Compare with existing video IDs
4. **Fetch Comments**: Get comments for each new video
5. **Publish Events**: Send to Kafka for downstream processing

### Tracking Modes

| Mode      | Description             | Use Case                 |
| --------- | ----------------------- | ------------------------ |
| Real-time | Continuous polling loop | Low-latency requirements |
| Scheduled | APScheduler intervals   | Resource-efficient       |

```python
from youtube.tracking_manager import ChannelTrackingManager

tracker = ChannelTrackingManager(config, api_manager, dao)

# Register channel
await tracker.register_channel("UC_x5XG1OV2P6uZZ5FSM9Ttw")

# Start tracking
await tracker.start_realtime_ingestion(interval_seconds=60)
# OR
await tracker.start_scheduled_ingestion(interval_minutes=5)
```

## Kafka Pipeline

### Topics

| Topic              | Content                 |
| ------------------ | ----------------------- |
| `youtube.channels` | Channel metadata events |
| `youtube.videos`   | Video metadata events   |
| `youtube.comments` | Comment events          |

### Event Format

All events follow the ingestion output format defined in `AGENTS.md`:

```json
{
  "source": "youtube",
  "externalId": "video_id_here",
  "rawText": "Video title and description",
  "createdAt": "2023-12-01T12:00:00Z",
  "rawPayload": { ... },
  "entityType": "video"
}
```

### Producer Usage

```python
from youtube.kafka_producer import YouTubeKafkaProducer

with YouTubeKafkaProducer(kafka_config) as producer:
    producer.produce_video_event(video_dto)
    producer.flush()
```

### Consumer Usage

```python
from youtube.kafka_consumer import create_youtube_event_processor

async def handle_video(event):
    print(f"New video: {event.external_id}")

await create_youtube_event_processor(
    kafka_config,
    on_video_event=handle_video,
)
```

## Database Schema

### Tables

- `youtube_channels`: Channel metadata and tracking state
- `youtube_videos`: Video metadata
- `youtube_comments`: Comments and replies
- `youtube_tracked_channels`: Tracking state for registered channels

### DAO Usage

```python
from youtube.dao import YouTubeDAO
from youtube.config import DatabaseConfig

dao = YouTubeDAO(DatabaseConfig.from_env())
dao.init_db()  # Create tables

# Save/retrieve data
dao.save_channel(channel_dto)
channel = dao.get_channel("UC_test")
```

## Testing

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api_manager.py -v
```

See [TESTING.md](./TESTING.md) for detailed testing instructions.

## Environment Variables

| Variable                         | Required | Default             | Description              |
| -------------------------------- | -------- | ------------------- | ------------------------ |
| `YOUTUBE_API_KEY`                | Yes      | -                   | YouTube Data API v3 key  |
| `KAFKA_BOOTSTRAP_SERVERS`        | No       | `kafka:9092`        | Kafka broker address     |
| `KAFKA_CLIENT_YOUTUBE_INGEST_ID` | No       | `youtube_ingestion` | Kafka client ID          |
| `DB_HOST`                        | No       | `postgres`          | PostgreSQL host          |
| `DB_PORT`                        | No       | `5432`              | PostgreSQL port          |
| `DB_NAME`                        | No       | `airflow`           | Database name            |
| `DB_USER`                        | No       | `airflow`           | Database user            |
| `DB_PASSWORD`                    | No       | `airflow`           | Database password        |
| `POLLING_INTERVAL_SECONDS`       | No       | `300`               | Default polling interval |
| `MAX_VIDEOS_PER_CHANNEL`         | No       | `50`                | Max videos to fetch      |
| `MAX_COMMENTS_PER_VIDEO`         | No       | `100`               | Max comments per video   |

## File Structure

```
youtube/
├── __init__.py
├── main.py              # CLI entry point
├── config.py            # Configuration management
├── dto.py               # Data Transfer Objects
├── models.py            # SQLAlchemy ORM models
├── dao.py               # Data Access Object
├── api_manager.py       # YouTube API wrapper
├── tracking_manager.py  # Channel tracking logic
├── kafka_producer.py    # Kafka event producer
├── kafka_consumer.py    # Kafka event consumer
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── README.md            # This file
├── TESTING.md           # Testing guide
└── tests/
    ├── __init__.py
    ├── conftest.py          # Pytest fixtures
    ├── test_api_manager.py
    ├── test_tracking_manager.py
    └── test_kafka.py
```
