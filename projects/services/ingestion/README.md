# Ingestion Service

Collects public social media data and persists raw messages for downstream processing.

## Purpose

- Connect to social platforms (YouTube first, then others)
- Capture comments, posts, and metadata
- Write raw messages to Kafka/database
- Crawl tourism websites for structured content extraction

## Technology

- **Language**: Python
- **APIs**: YouTube Data API, RSS feeds
- **Queue**: Apache Kafka
- **Web Crawling**: Crawl4AI with LLM extraction (Gemini)

## Connectors

| Connector | Status | Description |
|-----------|--------|-------------|
| YouTube | ✅ Active | Channel/video/comment ingestion |
| Web Crawl | ✅ Active | Tourism website content extraction |

## Status

🟢 *YouTube and Web Crawl connectors implemented*
