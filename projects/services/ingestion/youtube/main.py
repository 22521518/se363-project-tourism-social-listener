# YouTube Ingestion - Main Entry Point
# CLI for running the YouTube ingestion worker

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to python path to allow imports
# Go up 5 levels: youtube -> ingestion -> services -> projects -> airflow
project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from projects.services.ingestion.youtube.config import IngestionConfig
from projects.services.ingestion.youtube.dao import YouTubeDAO
from projects.services.ingestion.youtube.api_manager import YouTubeAPIManager
from projects.services.ingestion.youtube.tracking_manager import ChannelTrackingManager
from projects.services.ingestion.youtube.dto import ChannelDTO, VideoDTO, CommentDTO
from projects.services.ingestion.youtube.kafka_producer import YouTubeKafkaProducer
from projects.services.ingestion.youtube.kafka_consumer import create_youtube_event_processor, run_consumer

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


    async def handle_channel(event):
        """Handle channel event from Kafka."""
        try:
            logger.info(f"Processing channel event: {event.external_id}")
            payload = event.value.get("rawPayload")
            if not payload:
                logger.warning(f"No payload in event {event.external_id}")
                return
            
            # Reconstruct DTO
            dto = ChannelDTO(
                id=payload["id"],
                title=payload["title"],
                description=payload["description"],
                custom_url=payload["custom_url"],
                published_at=datetime.fromisoformat(payload["published_at"]),
                thumbnail_url=payload["thumbnail_url"],
                subscriber_count=payload["subscriber_count"],
                video_count=payload["video_count"],
                view_count=payload["view_count"],
                country=payload["country"],
            )
            
            # Save to DB
            dao.save_channel(dto, raw_payload=payload)
            logger.info(f"Saved channel {dto.id} to database")
            
        except Exception as e:
            logger.error(f"Error handling channel event: {e}")

    async def handle_video(event):
        """Handle video event from Kafka."""
        try:
            logger.info(f"Processing video event: {event.external_id}")
            payload = event.value.get("rawPayload")
            if not payload:
                return
            
            dto = VideoDTO(
                id=payload["id"],
                channel_id=payload["channel_id"],
                title=payload["title"],
                description=payload["description"],
                published_at=datetime.fromisoformat(payload["published_at"]),
                thumbnail_url=payload["thumbnail_url"],
                view_count=payload["view_count"],
                like_count=payload["like_count"],
                comment_count=payload["comment_count"],
                duration=payload["duration"],
                tags=tuple(payload["tags"]),
                category_id=payload["category_id"],
            )
            
            dao.save_video(dto, raw_payload=payload)
            logger.info(f"Saved video {dto.id} to database")
            
        except Exception as e:
            logger.error(f"Error handling video event: {e}")

    async def handle_comment(event):
        """Handle comment event from Kafka."""
        try:
            logger.info(f"Processing comment event: {event.external_id}")
            payload = event.value.get("rawPayload")
            if not payload:
                return
            
            dto = CommentDTO(
                id=payload["id"],
                video_id=payload["video_id"],
                author_display_name=payload["author_display_name"],
                author_channel_id=payload["author_channel_id"],
                text=payload["text"],
                like_count=payload["like_count"],
                published_at=datetime.fromisoformat(payload["published_at"]),
                updated_at=datetime.fromisoformat(payload["updated_at"]),
                parent_id=payload["parent_id"],
                reply_count=payload["reply_count"],
            )
            
            dao = YouTubeDAO(config.database)
            dao.save_comment(dto, raw_payload=payload)
            logger.info(f"Saved comment {dto.id} to database")
            
        except Exception as e:
            logger.error(f"Error handling comment event: {e}")
    
    logger.info("Starting Kafka consumer...")
    # NOTE: create_youtube_event_processor is designed for long-running. 
    # For run_once, we might need a custom loop usage or modify the processor.
    # However, create_youtube_event_processor currently wraps 'process_with_handler'.
    # We can use it but throw a special exception or use a task with timeout if we want to stop.
    # BUT easier: The user asked for "available in spark", so maybe run_consumer is meant to be long running?
    # "run consumer with spark-submit ... create scripts to run ... run above script at the same".
    # Since I'm making a DAG, "run once" behavior is preferred so the task finishes.
    
    # Let's wrap it in a task and cancel it after timeout if run_once is True
    consumer_task = asyncio.create_task(create_youtube_event_processor(
        config.kafka,
        on_channel_event=handle_channel,
        on_video_event=handle_video,
        on_comment_event=handle_comment,
    ))
    
    if run_once:
        logger.info(f"Consumer running in ONE-SHOT mode. Will stop after {timeout_s}s...")
        await asyncio.sleep(timeout_s)
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Consumer stopped (run-once timeout reached)")
    else:
        await consumer_task


async def run_db_driven_ingestion(config: IngestionConfig, interval_minutes: int = 5, run_once: bool = False):
    """
    Run ingestion driven by database state.
    Scrapes channels based on 'tracked' status in DB and produces events to Kafka.
    Does NOT save to DB directly (relies on Consumer).
    args:
        run_once: If True, runs one cycle and exits.
    """
    # 1. Setup connections
    dao = YouTubeDAO(config.database)
    dao.init_db()
    
    # We use api_manager ONLY for fetching DTOs, not for saving!
    # API Manager methods like fetch_channel_info, fetch_channel_videos return DTOs.
    api_manager = YouTubeAPIManager(config, dao)
    
    producer = YouTubeKafkaProducer(config.kafka)
    producer.create_topics()
    producer.connect()
    
    logger.info(f"Starting DB-driven ingestion loop (Interval: {interval_minutes} min)")
    
    try:
        while True:
            logger.info("Checking tracked channels for updates...")
            
            # 2. Get active tracked channels
            tracked_channels = dao.get_tracked_channels(active_only=True)
            
            for tracked in tracked_channels:
                channel_id = tracked.channel_id
                
                try:
                    # Check if channel is a "stub" (placeholder) or needs full backfill
                    # We check the actual channel record
                    channel_record = dao.get_channel(channel_id)
                    
                    is_stub = False
                    if channel_record and channel_record.title.startswith("Pending Ingestion"):
                        is_stub = True
                    
                    if is_stub:
                        logger.info(f"Backfilling stub channel: {channel_id}")
                        
                        # A. Fetch & Produce Channel Info
                        try:
                            channel_dto = await api_manager.fetch_channel_info(channel_id)
                            producer.produce_channel_event(channel_dto)
                        except Exception as e:
                            logger.error(f"Failed to fetch info for {channel_id}: {e}")
                            continue

                        # B. Fetch & Produce Videos (Full history up to limit)
                        try:
                            videos = await api_manager.fetch_channel_videos(channel_id, max_results=50) # Limit for initial backfill
                            for video in videos:
                                producer.produce_video_event(video)
                            
                            # C. Fetch & Produce Comments for these videos
                            for video in videos:
                                comments = await api_manager.fetch_video_comments(video.id, max_results=20)
                                for comment in comments:
                                    producer.produce_comment_event(comment)
                        except Exception as e:
                            logger.error(f"Failed to fetch content for {channel_id}: {e}")
                            
                        logger.info(f"Produced events for backfill of {channel_id}")
                        
                    else:
                        # Normal update: Fetch "latest" videos
                        # We assume "latest" means checking the feed again.
                        logger.info(f"Checking updates for: {channel_id} ({channel_record.title})")
                        
                        # Get existing video IDs to filter
                        existing_ids = set(dao.get_video_ids_for_channel(channel_id))
                        
                        # Fetch latest videos (default limit is usually small, e.g. 10-20)
                        videos = await api_manager.fetch_channel_videos(channel_id, max_results=20)
                        
                        new_count = 0
                        for video in videos:
                            if video.id not in existing_ids:
                                producer.produce_video_event(video)
                                new_count += 1
                        
                        if new_count > 0:
                            logger.info(f"Found and produced {new_count} new videos for {channel_id}")
                    
                    # 4. Flush producer
                    producer.flush()
                    
                    # 5. Update last_checked in DB (Control Plane)
                    # We update this so we don't spam the same channel if inter-loop time is short,
                    # although strictly speaking 'last_checked' is data. 
                    # But it drives the logic, so updating it here is correct for the scheduler.
                    dao.update_tracking_state(
                        channel_id, 
                        last_checked=datetime.now(datetime.UTC),
                        # last_video_published is updated by consumer ideally, or we can leave it
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing channel {channel_id}: {e}")
            
            if run_once:
                logger.info("Run-once mode: Cycle complete. Exiting...")
                break

            # Wait for next interval
            logger.info(f"Cycle complete. Waiting {interval_minutes} minutes...")
            await asyncio.sleep(interval_minutes * 60)
            
    except asyncio.CancelledError:
        logger.info("Ingestion loop cancelled")
    finally:
        producer.disconnect()


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
    import argparse # Moved import here as it's only used in main
    parser = argparse.ArgumentParser(description="YouTube Ingestion Worker")
    parser.add_argument(
        "--mode",
        choices=["realtime", "scheduled", "full", "consumer", "register", "init-db", "init-kafka", "smart"],
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
        help="Polling interval in seconds (for realtime) or minutes (for scheduled/smart)",
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run only one cycle (for smart/consumer modes) and exit.",
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
        elif args.mode == "smart":
             # Default to 5 minutes if interval is too small (likely passed as seconds by mistake)
            interval = args.interval if args.interval > 10 else 5
            asyncio.run(run_db_driven_ingestion(config, interval, run_once=args.run_once))
        elif args.mode == "full":
            asyncio.run(run_full_ingestion(config, args.channel))
        elif args.mode == "consumer":
            asyncio.run(run_consumer(config, run_once=args.run_once))
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
