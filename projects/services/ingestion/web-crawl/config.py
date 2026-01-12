"""
Web Crawl Configuration - Centralized configuration loading from environment variables.

Following the YouTube module pattern for consistency.
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


def load_env_files():
    """Load .env files from multiple possible locations in order of priority."""
    current_file = Path(__file__).resolve()
    webcrawl_dir = current_file.parent  # web-crawl/
    
    possible_paths = [
        # 1. Local .env (web-crawl/.env)
        webcrawl_dir / ".env",
        # 2. projects/.env
        webcrawl_dir.parents[2] / ".env",  # web-crawl -> ingestion -> services -> projects
        # 3. airflow root .env
        webcrawl_dir.parents[3] / ".env",  # projects -> airflow
        # 4. Docker paths
        Path("/opt/airflow/projects/services/ingestion/web-crawl/.env"),
        Path("/opt/airflow/projects/.env"),
        Path("/opt/airflow/.env"),
    ]
    
    loaded = False
    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            print(f"✅ Web Crawl Config: Loaded .env from: {env_path}")
            loaded = True
            break
    
    if not loaded:
        load_dotenv()
        print("⚠️ Web Crawl Config: Using default dotenv search")

load_env_files()


@dataclass(frozen=True)
class GeminiConfig:
    """Gemini API configuration."""
    api_key: str
    
    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """Load Gemini config from environment variables."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        return cls(api_key=api_key)


@dataclass(frozen=True)
class KafkaConfig:
    """Kafka configuration for web crawl module."""
    bootstrap_servers: str
    client_id: str
    
    # Topic names
    requests_topic: str = "webcrawl.requests"
    results_topic: str = "webcrawl.results"
    raw_topic: str = "webcrawl.raw"
    
    @classmethod
    def from_env(cls) -> "KafkaConfig":
        """Load Kafka config from environment variables."""
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            client_id=os.getenv("KAFKA_CLIENT_WEBCRAWL_ID", "webcrawl_ingestion"),
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
class WebCrawlConfig:
    """Combined web crawl configuration."""
    gemini: GeminiConfig
    kafka: KafkaConfig
    database: DatabaseConfig
    
    # Crawl settings
    max_content_length: int = 100000
    rate_limit_per_min: int = 3
    headless: bool = True
    
    @classmethod
    def from_env(cls) -> "WebCrawlConfig":
        """Load all config from environment variables."""
        return cls(
            gemini=GeminiConfig.from_env(),
            kafka=KafkaConfig.from_env(),
            database=DatabaseConfig.from_env(),
            max_content_length=int(os.getenv("WEBCRAWL_MAX_CONTENT_LENGTH", "100000")),
            rate_limit_per_min=int(os.getenv("WEBCRAWL_RATE_LIMIT_PER_MIN", "3")),
            headless=os.getenv("WEBCRAWL_HEADLESS", "true").lower() == "true",
        )
