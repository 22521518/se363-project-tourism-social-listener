# YouTube Ingestion - Configuration
# Centralized configuration loading from environment variables

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


def load_env_files():
    """Load .env files from multiple possible locations in order of priority."""
    current_file = Path(__file__).resolve()
    youtube_dir = current_file.parent  # youtube/
    
    possible_paths = [
        # 1. Local .env (youtube/.env)
        youtube_dir / ".env",
        # 2. projects/.env
        youtube_dir.parents[2] / ".env",  # youtube -> ingestion -> services -> projects
        # 3. airflow root .env
        youtube_dir.parents[3] / ".env",  # projects -> airflow
        # 4. Docker paths
        Path("/opt/airflow/projects/services/ingestion/youtube/.env"),
        Path("/opt/airflow/projects/.env"),
        Path("/opt/airflow/.env"),
    ]
    
    loaded = False
    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            print(f"✅ YouTube Config: Loaded .env from: {env_path}")
            loaded = True
            break
    
    if not loaded:
        load_dotenv()
        print("⚠️ YouTube Config: Using default dotenv search")

load_env_files()


@dataclass(frozen=True)
class YouTubeConfig:
    """YouTube Data API configuration."""
    api_key: str
    
    @classmethod
    def from_env(cls) -> "YouTubeConfig":
        """Load YouTube config from environment variables."""
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable is required")
        return cls(api_key=api_key)


@dataclass(frozen=True)
class KafkaConfig:
    """Kafka configuration."""
    bootstrap_servers: str
    client_id: str
    
    # Topic names
    # Topic names
    channels_topic: str = "youtube.channels"
    videos_topic: str = "youtube.videos"
    comments_topic: str = "youtube.comments"
    
    # Internal Topic names (for raw data)
    raw_channels_topic: str = "youtube.raw.channels"
    raw_videos_topic: str = "youtube.raw.videos"
    raw_comments_topic: str = "youtube.raw.comments"
    
    @classmethod
    def from_env(cls) -> "KafkaConfig":
        """Load Kafka config from environment variables."""
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            client_id=os.getenv("KAFKA_CLIENT_YOUTUBE_INGEST_ID", "youtube_ingestion"),
        )


@dataclass(frozen=True)
class DatabaseConfig:
    """PostgreSQL database configuration."""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load database config from environment variables."""
        return cls(
            host=os.getenv("DB_HOST", "postgres"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "airflow"),
            user=os.getenv("DB_USER", "airflow"),
            password=os.getenv("DB_PASSWORD", "airflow"),
        )
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass(frozen=True)
class IngestionConfig:
    """Combined ingestion configuration."""
    youtube: YouTubeConfig
    kafka: KafkaConfig
    database: DatabaseConfig
    
    # Ingestion settings
    polling_interval_seconds: int = 300  # 5 minutes
    max_videos_per_channel: int = 50
    max_comments_per_video: int = 100
    
    @classmethod
    def from_env(cls) -> "IngestionConfig":
        """Load all config from environment variables."""
        return cls(
            youtube=YouTubeConfig.from_env(),
            kafka=KafkaConfig.from_env(),
            database=DatabaseConfig.from_env(),
            polling_interval_seconds=int(os.getenv("POLLING_INTERVAL_SECONDS", "300")),
            max_videos_per_channel=int(os.getenv("MAX_VIDEOS_PER_CHANNEL", "50")),
            max_comments_per_video=int(os.getenv("MAX_COMMENTS_PER_VIDEO", "100")),
        )
