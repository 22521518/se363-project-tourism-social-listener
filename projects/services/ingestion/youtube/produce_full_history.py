
import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to python path to allow imports
project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from projects.services.ingestion.youtube.config import IngestionConfig
from projects.services.ingestion.youtube.dao import YouTubeDAO
from projects.services.ingestion.youtube.api_manager import YouTubeAPIManager
from projects.services.ingestion.youtube.kafka_producer import YouTubeKafkaProducer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("youtube_full_producer")

async def process_channel_full(api_manager, producer, channel_id, config):
    """Helper to process a single channel with full history."""
    logger.info(f"Starting FULL HISTORY ingestion for: {channel_id}")
    try:
        # 1. Fetch & Produce Channel Info
        logger.info("Step 1/3: Fetching Channel Info...")
        channel = await api_manager.populate_channel(channel_id)
        producer.produce_channel_event(channel)
        logger.info(f"Channel found: {channel.title} ({channel.id})")
        
        real_channel_id = channel.id

        # 2. Fetch ALL Videos
        # Override default limit to fetch effectively all videos
        max_videos = 100000 
        logger.info(f"Step 2/3: Fetching up to {max_videos} videos (IDs and Details)...")
        
        videos = await api_manager.fetch_channel_videos(
            real_channel_id, 
            max_results=max_videos
        )
        logger.info(f"Successfully fetched {len(videos)} videos.")

        # 3. Produce Videos & Fetch/Produce Comments
        logger.info("Step 3/3: Producing videos and fetching comments...")
        
        total_videos = len(videos)
        total_comments = 0
        
        for i, video in enumerate(videos):
            producer.produce_video_event(video)
            
            try:
                # Fetch comments (override default limit)
                comments = await api_manager.fetch_video_comments(
                    video.id, 
                    max_results=100000
                )
                
                for comment in comments:
                    producer.produce_comment_event(comment)
                
                count = len(comments)
                total_comments += count
                
            except Exception as e:
                # Log error but continue with next video
                logger.error(f"Failed to fetch comments for video {video.id}: {e}")

            if (i + 1) % 10 == 0:
                producer.flush()
                logger.info(f"Progress: Processed {i + 1}/{total_videos} videos. (Total comments: {total_comments})")

        producer.flush()
        
        logger.info("="*50)
        logger.info("INGESTION COMPLETE")
        logger.info(f"Channel: {channel.title}")
        logger.info(f"Videos Produced: {total_videos}")
        logger.info(f"Comments Produced: {total_comments}")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"Error processing channel {channel_id}: {e}")
        import traceback
        traceback.print_exc()

async def run_full_history_ingestion(channel_id: str = None):
    """
    Pull ALL data from a YouTube channel.
    If channel_id is None, fetch ALL tracked channels from DB and process them one by one.
    """
    try:
        config = IngestionConfig.from_env()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return

    # Initialize DAO (needed by API Manager for caching/checkpoints/consistency)
    dao = YouTubeDAO(config.database)
    dao.init_db()

    api_manager = YouTubeAPIManager(config, dao)
    
    # Initialize Kafka Producer
    producer = YouTubeKafkaProducer(config.kafka)
    producer.connect()

    try:
        if channel_id:
            await process_channel_full(api_manager, producer, channel_id, config)
        else:
            logger.info("No specific channel provided. Processing ALL tracked channels...")
            tracked_channels = dao.get_tracked_channels(active_only=True)
            
            if not tracked_channels:
                logger.info("No active tracked channels found in database.")
                return
            
            logger.info(f"Found {len(tracked_channels)} channels to process.")
            for i, tracked in enumerate(tracked_channels):
                logger.info(f"--- Channel {i+1}/{len(tracked_channels)}: {tracked.channel_id} ---")
                await process_channel_full(api_manager, producer, tracked.channel_id, config)

    finally:
        producer.disconnect()


def main():
    parser = argparse.ArgumentParser(description="YouTube Full History Producer")
    parser.add_argument(
        "--channel",
        help="Channel ID or Handle to ingest. If omitted, processes all tracked channels.",
        default=None
    )
    # Support legacy flags to allow drop-in replacement
    parser.add_argument("--mode", help="Ignored (legacy compatibility)", required=False)
    parser.add_argument("--interval", help="Ignored (legacy compatibility)", required=False)
    parser.add_argument("--run-once", help="Ignored (legacy compatibility)", required=False, action="store_true")
    
    args = parser.parse_args()
    
    # If explicit channel arg is not set but maybe passed as positional (old script didn't allow this but just in case)
    # The old script required --mode.
    
    asyncio.run(run_full_history_ingestion(args.channel))

if __name__ == "__main__":
    main()
