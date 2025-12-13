  
import asyncio
import logging
import sys
import os

# Add the root directory to sys.path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../../../"))
sys.path.append(root_dir)

from projects.services.ingestion.youtube.config import IngestionConfig
from projects.services.ingestion.youtube.api_manager import YouTubeAPIManager

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    try:
        print("Loading configuration...")
        try:
            config = IngestionConfig.from_env()
        except ValueError as e:
            print(f"Configuration Error: {e}")
            print("Please ensure .env file is present or environment variables are set.")
            return

        print(f"API Key Loaded: {'Yes' if config.youtube.api_key else 'No'}")
        
        manager = YouTubeAPIManager(config)
        
        handle = "@KhoaiLangThang"
        print(f"\nTesting handle resolution for: {handle}")
        
        channel_id = await manager.resolve_handle_to_id(handle)
        
        if channel_id:
            print(f"SUCCESS: Resolved {handle} to {channel_id}")
            
            print(f"Fetching channel info for ID: {channel_id}...")
            info = await manager.fetch_channel_info(channel_id)
            print(f"Channel Title: {info.title}")
            print(f"   Subscribers: {info.subscriber_count}")
        else:
            print(f"FAILURE: Could not resolve {handle}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
