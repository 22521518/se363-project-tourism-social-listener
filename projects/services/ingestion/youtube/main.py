# YouTube Ingestion - Main Entry Point
# CLI for running the YouTube ingestion worker

import argparse
import asyncio
import logging
import sys
from datetime import datetime

from .config import IngestionConfig
from .dao import YouTubeDAO
from .api_manager import YouTubeAPIManager
from .tracking_manager import ChannelTrackingManager, IngestionMode
from .kafka_producer import YouTubeKafkaProducer
from .kafka_consumer import YouTubeKafkaConsumer, create_youtube_event_processor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def run_realtime_ingestion(config: IngestionConfig, interval: int = 60):
    """Run real-time ingestion mode."""
    dao = YouTubeDAO(config.database)
    dao.init_db()
    
    api_manager = YouTubeAPIManager(config, dao)
    
    producer = YouTubeKafkaProducer(config.kafka)
    producer.create_topics()
    producer.connect()
    
    async def on_new_video(video):
        logger.info(f"New video detected: {video.title}")
        producer.produce_video_event(video)
        producer.flush()
    
    tracking_manager = ChannelTrackingManager(
        config, api_manager, dao, on_new_video=on_new_video
    )
    
    logger.info("Starting real-time ingestion...")
    await tracking_manager.start_realtime_ingestion(interval_seconds=interval)
    
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await tracking_manager.stop_ingestion()
        producer.disconnect()


async def run_scheduled_ingestion(config: IngestionConfig, interval_minutes: int = 5):
    """Run scheduled ingestion mode."""
    dao = YouTubeDAO(config.database)
    dao.init_db()
    
    api_manager = YouTubeAPIManager(config, dao)
    
    producer = YouTubeKafkaProducer(config.kafka)
    producer.create_topics()
    producer.connect()
    
    async def on_new_video(video):
        logger.info(f"New video detected: {video.title}")
        producer.produce_video_event(video)
        producer.flush()
    
    tracking_manager = ChannelTrackingManager(
        config, api_manager, dao, on_new_video=on_new_video
    )
    
    logger.info(f"Starting scheduled ingestion with {interval_minutes}min interval...")
    await tracking_manager.start_scheduled_ingestion(interval_minutes=interval_minutes)
    
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await tracking_manager.stop_ingestion()
        producer.disconnect()


async def run_full_ingestion(config: IngestionConfig, channel_id: str):
    """Run full ingestion for a single channel."""
    dao = YouTubeDAO(config.database)
    dao.init_db()
    
    api_manager = YouTubeAPIManager(config, dao)
    
    producer = YouTubeKafkaProducer(config.kafka)
    producer.create_topics()
    producer.connect()
    
    logger.info(f"Running full ingestion for channel: {channel_id}")
    
    try:
        result = await api_manager.ingest_channel_full(channel_id)
        logger.info(f"Ingestion complete: {result}")
        
        # Produce events to Kafka
        channel = dao.get_channel(channel_id)
        if channel:
            producer.produce_channel_event(channel)
        
        videos = dao.get_channel_videos(channel_id)
        for video in videos:
            producer.produce_video_event(video)
        
        producer.flush()
        logger.info("Events published to Kafka")
        
    finally:
        producer.disconnect()


async def run_consumer(config: IngestionConfig):
    """Run Kafka consumer for processing events."""
    async def handle_channel(event):
        logger.info(f"Processing channel event: {event.external_id}")
    
    async def handle_video(event):
        logger.info(f"Processing video event: {event.external_id}")
    
    async def handle_comment(event):
        logger.info(f"Processing comment event: {event.external_id}")
    
    logger.info("Starting Kafka consumer...")
    await create_youtube_event_processor(
        config.kafka,
        on_channel_event=handle_channel,
        on_video_event=handle_video,
        on_comment_event=handle_comment,
    )


async def register_channel(config: IngestionConfig, channel_id: str):
    """Register a channel for tracking."""
    dao = YouTubeDAO(config.database)
    dao.init_db()
    
    api_manager = YouTubeAPIManager(config, dao)
    tracking_manager = ChannelTrackingManager(config, api_manager, dao)
    
    await tracking_manager.register_channel(channel_id)
    logger.info(f"Channel {channel_id} registered for tracking")


async def init_database(config: IngestionConfig):
    """Initialize database tables."""
    dao = YouTubeDAO(config.database)
    dao.init_db()
    logger.info("Database tables created")


async def init_kafka_topics(config: IngestionConfig):
    """Initialize Kafka topics."""
    producer = YouTubeKafkaProducer(config.kafka)
    producer.create_topics()
    logger.info("Kafka topics created")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="YouTube Ingestion Worker")
    parser.add_argument(
        "--mode",
        choices=["realtime", "scheduled", "full", "consumer", "register", "init-db", "init-kafka"],
        required=True,
        help="Ingestion mode",
    )
    parser.add_argument(
        "--channel",
        help="Channel ID (required for full and register modes)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in seconds (for realtime) or minutes (for scheduled)",
    )
    
    args = parser.parse_args()
    
    try:
        config = IngestionConfig.from_env()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    if args.mode in ["full", "register"] and not args.channel:
        logger.error(f"--channel is required for {args.mode} mode")
        sys.exit(1)
    
    try:
        if args.mode == "realtime":
            asyncio.run(run_realtime_ingestion(config, args.interval))
        elif args.mode == "scheduled":
            asyncio.run(run_scheduled_ingestion(config, args.interval))
        elif args.mode == "full":
            asyncio.run(run_full_ingestion(config, args.channel))
        elif args.mode == "consumer":
            asyncio.run(run_consumer(config))
        elif args.mode == "register":
            asyncio.run(register_channel(config, args.channel))
        elif args.mode == "init-db":
            asyncio.run(init_database(config))
        elif args.mode == "init-kafka":
            asyncio.run(init_kafka_topics(config))
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
