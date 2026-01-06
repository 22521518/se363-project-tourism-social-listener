#!/usr/bin/env python3
"""
Console script to add YouTube channels to tracking (Interactive Mode).
Usage: python add_channel.py

Validates channels using YouTube API before adding to database.
Supports both channel IDs (UC...) and handles (@username).
"""
import sys
import re
import asyncio
from pathlib import Path
from sqlalchemy import text

# Add the project root to python path to allow absolute imports
# File location: projects/services/ingestion/youtube/web/dev/add_channel.py
# Hierarchy: dev -> web -> youtube -> ingestion -> services -> projects -> airflow
# Path(__file__).parents[6] should be 'airflow' root
project_root = Path(__file__).resolve().parents[6]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import backend services
try:
    from projects.services.ingestion.youtube.config import DatabaseConfig, IngestionConfig
    from projects.services.ingestion.youtube.dao import YouTubeDAO
    from projects.services.ingestion.youtube.api_manager import YouTubeAPIManager
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure you're running from the correct directory and all dependencies are installed.")
    sys.exit(1)


def extract_channel_input(input_str: str) -> str:
    """
    Extract channel ID or handle from various input formats.
    Preserves the @ prefix for handles so we can validate via YouTube API.
    
    - @KhoaiLangThang -> @KhoaiLangThang (preserve handle)
    - UC_x5XG1OV2P6uZZ5FSM9Ttw -> UC_x5XG1OV2P6uZZ5FSM9Ttw
    - https://www.youtube.com/@KhoaiLangThang -> @KhoaiLangThang
    - https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw -> UC_x5XG1OV2P6uZZ5FSM9Ttw
    """
    input_str = input_str.strip()
    
    # Handle @username format - preserve it
    if input_str.startswith('@'):
        return input_str
    
    # Handle full YouTube URLs
    if 'youtube.com' in input_str:
        # Extract from /channel/ URL
        channel_match = re.search(r'/channel/([a-zA-Z0-9_-]+)', input_str)
        if channel_match:
            return channel_match.group(1)
        
        # Extract from /@username URL - preserve @ prefix
        username_match = re.search(r'/(@[a-zA-Z0-9_-]+)', input_str)
        if username_match:
            return username_match.group(1)
    
    # Return as-is (assume it's already a channel ID)
    return input_str


async def validate_channel_on_youtube(api_manager: YouTubeAPIManager, channel_input: str) -> tuple[bool, str | None, str | None]:
    """
    Validate if channel exists on YouTube using the API.
    
    Args:
        api_manager: YouTubeAPIManager instance
        channel_input: Channel ID or @handle
        
    Returns:
        Tuple of (exists: bool, resolved_channel_id: str | None, channel_title: str | None)
    """
    try:
        # Use fetch_channel_info which handles both channel IDs and @handles
        channel_dto = await api_manager.fetch_channel_info(channel_input)
        return True, channel_dto.id, channel_dto.title
    except ValueError as e:
        # Channel not found or handle could not be resolved
        return False, None, None
    except Exception as e:
        print(f"⚠️  Warning: API validation error: {e}")
        return False, None, None


def check_channel_exists_in_db(dao: 'YouTubeDAO', channel_id: str) -> bool:
    """Check if channel is already being tracked in the database."""
    try:
        engine = dao.db_config.get_engine()
        with engine.connect() as conn:
            # Check if channel exists in tracked channels table
            query = text("""
                SELECT COUNT(*) as count 
                FROM youtube_tracked_channels 
                WHERE channel_id = :channel_id AND is_active = true
            """)
            result = conn.execute(query, {"channel_id": channel_id}).fetchone()
            return result[0] > 0
    except Exception as e:
        print(f"⚠️  Warning: Could not check database: {e}")
        return False


async def add_channel_async(dao: 'YouTubeDAO', api_manager: YouTubeAPIManager, channel_input: str) -> bool:
    """
    Add a new YouTube channel to tracking after validating with YouTube API.
    
    Args:
        dao: YouTubeDAO instance
        api_manager: YouTubeAPIManager instance
        channel_input: Channel ID or @handle
        
    Returns:
        True if channel was added successfully
    """
    try:
        # Step 1: Validate channel exists on YouTube
        print(f"🔍 Đang kiểm tra channel trên YouTube...")
        exists, resolved_id, channel_title = await validate_channel_on_youtube(api_manager, channel_input)
        
        if not exists or not resolved_id:
            print(f"❌ Channel '{channel_input}' không tồn tại trên YouTube!")
            return False
        
        print(f"✓  Tìm thấy: {channel_title} (ID: {resolved_id})")
        
        # Step 2: Check if already in database
        if check_channel_exists_in_db(dao, resolved_id):
            print(f"⚠️  Channel '{channel_title}' (ID: {resolved_id}) đã tồn tại trong hệ thống!")
            return False
        
        # Step 3: Register the channel for tracking using resolved ID
        dao.register_tracked_channel(resolved_id)
        
        print(f"✅ Thành công! Channel '{channel_title}' (ID: {resolved_id}) đã được thêm vào tracking.")
        print("   Dữ liệu sẽ xuất hiện sau khi quá trình ingestion chạy.")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi thêm channel: {e}")
        return False


def add_channel(dao: 'YouTubeDAO', api_manager: YouTubeAPIManager, channel_input: str) -> bool:
    """Synchronous wrapper for add_channel_async."""
    return asyncio.run(add_channel_async(dao, api_manager, channel_input))


def main():
    """Main entry point for the console script."""
    print("=" * 70)
    print("📺 YouTube Channel Tracker - Interactive Mode")
    print("=" * 70)
    print()
    
    # Initialize DAO and API Manager
    try:
        db_config = DatabaseConfig.from_env()
        dao = YouTubeDAO(db_config)
        
        # Initialize API Manager for YouTube validation
        ingestion_config = IngestionConfig.from_env()
        api_manager = YouTubeAPIManager(ingestion_config, dao)
        
        print("✅ Đã kết nối database và YouTube API thành công!")
        print()
    except ValueError as e:
        print(f"❌ Lỗi cấu hình: {e}")
        print("   Vui lòng kiểm tra file .env của bạn (DB_*, YOUTUBE_API_KEY).")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Không thể khởi tạo: {e}")
        sys.exit(1)
    
    # Interactive loop
    print("Nhập channel để thêm vào tracking (nhập 'q' hoặc 'quit' để thoát)")
    print("Hỗ trợ: @handle, UC..., hoặc URL YouTube")
    print("-" * 70)
    print()
    
    added_count = 0
    
    while True:
        try:
            # Get user input
            user_input = input("Nhập channel (ví dụ: @KhoaiLangThang, UC_x5XG1OV2P6uZZ5FSM9Ttw): ").strip()
            
            # Check for exit command
            if user_input.lower() in ['q', 'quit', 'exit', 'thoat']:
                print()
                print("=" * 70)
                print(f"👋 Đã thêm {added_count} channel(s) thành công. Tạm biệt!")
                print("=" * 70)
                break
            
            # Skip empty input
            if not user_input:
                print("⚠️  Vui lòng nhập channel ID hoặc @handle!")
                print()
                continue
            
            # Extract channel input (preserves @ for handles)
            channel_input = extract_channel_input(user_input)
            
            # Add the channel (validates via YouTube API)
            print(f"🔄 Đang xử lý '{channel_input}'...")
            success = add_channel(dao, api_manager, channel_input)
            
            if success:
                added_count += 1
            
            print()
            
        except KeyboardInterrupt:
            print()
            print()
            print("=" * 70)
            print(f"👋 Đã thêm {added_count} channel(s) thành công. Tạm biệt!")
            print("=" * 70)
            break
        except Exception as e:
            print(f"❌ Lỗi không mong đợi: {e}")
            print()


if __name__ == "__main__":
    main()
