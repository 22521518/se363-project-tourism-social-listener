#!/usr/bin/env python3
"""
Console script to add YouTube channels to tracking (Interactive Mode).
Usage: python add_channel.py
"""
import sys
import re
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
    from projects.services.ingestion.youtube.config import DatabaseConfig
    from projects.services.ingestion.youtube.dao import YouTubeDAO
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure you're running from the correct directory and all dependencies are installed.")
    sys.exit(1)


def extract_channel_id(input_str: str) -> str:
    """
    Extract channel ID from various input formats:
    - @KhoaiLangThang -> KhoaiLangThang
    - UC_x5XG1OV2P6uZZ5FSM9Ttw -> UC_x5XG1OV2P6uZZ5FSM9Ttw
    - https://www.youtube.com/@KhoaiLangThang -> KhoaiLangThang
    - https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw -> UC_x5XG1OV2P6uZZ5FSM9Ttw
    """
    input_str = input_str.strip()
    
    # Handle @username format
    if input_str.startswith('@'):
        return input_str[1:]
    
    # Handle full YouTube URLs
    if 'youtube.com' in input_str:
        # Extract from /channel/ URL
        channel_match = re.search(r'/channel/([a-zA-Z0-9_-]+)', input_str)
        if channel_match:
            return channel_match.group(1)
        
        # Extract from /@username URL
        username_match = re.search(r'/@([a-zA-Z0-9_-]+)', input_str)
        if username_match:
            return username_match.group(1)
    
    # Return as-is (assume it's already a channel ID)
    return input_str


def validate_channel_id(channel_id: str) -> bool:
    """Validate if the channel ID format is reasonable."""
    if not channel_id:
        return False
    
    # Channel IDs are usually UC followed by 22 characters, or custom usernames
    # We'll accept alphanumeric, underscore, and hyphen
    if re.match(r'^[a-zA-Z0-9_-]+$', channel_id):
        return True
    
    return False


def check_channel_exists(dao: 'YouTubeDAO', channel_id: str) -> bool:
    """Check if channel is already being tracked."""
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
        print(f"⚠️  Warning: Could not check channel existence: {e}")
        return False


def add_channel(dao: 'YouTubeDAO', channel_id: str) -> bool:
    """Add a new YouTube channel to tracking."""
    try:
        # Check if already exists
        if check_channel_exists(dao, channel_id):
            print(f"⚠️  Channel '{channel_id}' đã tồn tại trong hệ thống!")
            return False
        
        # Register the channel for tracking
        dao.register_tracked_channel(channel_id)
        
        print(f"✅ Thành công! Channel '{channel_id}' đã được thêm vào tracking.")
        print("   Dữ liệu sẽ xuất hiện sau khi quá trình ingestion chạy.")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi thêm channel: {e}")
        return False


def main():
    """Main entry point for the console script."""
    print("=" * 70)
    print("📺 YouTube Channel Tracker - Interactive Mode")
    print("=" * 70)
    print()
    
    # Initialize DAO once
    try:
        db_config = DatabaseConfig.from_env()
        dao = YouTubeDAO(db_config)
        print("✅ Đã kết nối database thành công!")
        print()
    except ValueError as e:
        print(f"❌ Lỗi cấu hình: {e}")
        print("   Vui lòng kiểm tra file .env của bạn.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Không thể kết nối database: {e}")
        sys.exit(1)
    
    # Interactive loop
    print("Nhập channel để thêm vào tracking (nhập 'q' hoặc 'quit' để thoát)")
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
                print("⚠️  Vui lòng nhập channel ID!")
                print()
                continue
            
            # Extract and validate channel ID
            channel_id = extract_channel_id(user_input)
            
            if not validate_channel_id(channel_id):
                print(f"❌ Channel ID '{channel_id}' không hợp lệ!")
                print("   Channel ID phải chứa chữ cái, số, gạch dưới hoặc gạch ngang.")
                print()
                continue
            
            # Add the channel
            print(f"🔄 Đang thêm channel '{channel_id}'...")
            success = add_channel(dao, channel_id)
            
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
