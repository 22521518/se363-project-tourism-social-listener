# Ingestion – Step-by-Step Guide

> Planning artifacts go in `agents_plans/`.

## Steps
1. Plan in `agents_plans/tasks/`
2. Implement connector
3. Test with sample output in `data/raw/`

## Commands
```powershell
cd services/ingestion && pip install -r requirements.txt && python main.py
```

## Output Format
- `source`: platform name
- `externalId`: platform-specific ID
- `rawText`: original content
- `createdAt`: ISO timestamp
- `rawPayload`: full API response

## YouTube Connector

### Structure
```
youtube/
├── main.py, config.py, dto.py, models.py, dao.py
├── api_manager.py, tracking_manager.py
├── kafka_producer.py, kafka_consumer.py
└── tests/
```

### Commands
```powershell
python -m youtube.main --mode=init-db
python -m youtube.main --mode=full --channel=<CHANNEL_ID>
python -m youtube.main --mode=realtime --interval=60
```

### Kafka Topics
| Topic | Content |
|-------|---------|
| `youtube.channels` | Channel metadata |
| `youtube.videos` | Video metadata |
| `youtube.comments` | Comments |
