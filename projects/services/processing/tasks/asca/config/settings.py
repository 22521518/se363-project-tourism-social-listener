"""
Configuration settings for the ASCA (Aspect Category Sentiment Analysis) module.
Uses dataclass for simple configuration like YouTube module.
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Literal
from dotenv import load_dotenv

# Load environment variables from .env file
# Path: projects/.env (go up from asca/config -> asca -> tasks -> processing -> services -> projects)
current_dir = Path(__file__).resolve().parent  # config/
asca_dir = current_dir.parent  # asca/
projects_dir = asca_dir.parents[3]  # projects/

# Try loading from projects/.env
env_path = projects_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from: {env_path}")
else:
    # Fallback: try /opt/airflow/projects/.env for Docker
    docker_env = Path("/opt/airflow/projects/.env")
    if docker_env.exists():
        load_dotenv(docker_env)
        print(f"✅ Loaded .env from: {docker_env}")
    else:
        load_dotenv()
        print("⚠️ Using default dotenv search")


# Language detection
def detect_language(text: str) -> Literal["vi", "en"]:
    """
    Detect if text is Vietnamese or English.
    Uses simple heuristics based on Vietnamese-specific characters.
    """
    vietnamese_chars = set('àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ')
    vietnamese_chars.update(set('ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ'))
    
    text_lower = text.lower()
    vietnamese_count = sum(1 for char in text_lower if char in vietnamese_chars)
    
    # If more than 1% of characters are Vietnamese-specific, classify as Vietnamese
    if len(text) > 0 and (vietnamese_count / len(text)) > 0.01:
        return "vi"
    return "en"


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
        """Get SQLAlchemy connection string."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass(frozen=True)
class KafkaConfig:
    """Kafka configuration."""
    bootstrap_servers: str
    input_topic: str
    output_topic: str
    consumer_group: str
    
    @classmethod
    def from_env(cls) -> "KafkaConfig":
        """Load Kafka config from environment variables."""
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            input_topic=os.getenv("KAFKA_TOPIC_ASCA_INPUT", "asca-input"),
            output_topic=os.getenv("KAFKA_TOPIC_ASCA_OUTPUT", "asca-output"),
            consumer_group=os.getenv("KAFKA_CONSUMER_GROUP", "asca-consumer"),
        )


@dataclass(frozen=True)
class ASCAConfig:
    """ASCA model configuration."""
    model_path: str
    language: str
    auto_detect: bool
    vncorenlp_path: Optional[str]
    
    @classmethod
    def from_env(cls) -> "ASCAConfig":
        """Load ASCA config from environment variables."""
        return cls(
            model_path=os.getenv("ASCA_MODEL_PATH", "/opt/airflow/models/asca/acsa.pkl"),
            language=os.getenv("ASCA_LANGUAGE", "vi"),
            auto_detect=os.getenv("ASCA_AUTO_DETECT_LANGUAGE", "true").lower() == "true",
            vncorenlp_path=os.getenv("VNCORENLP_PATH"),
        )


# Legacy compatibility - Settings class equivalent
class Settings:
    """Settings wrapper for backward compatibility."""
    
    def __init__(self):
        self.db = DatabaseConfig.from_env()
        self.kafka = KafkaConfig.from_env()
        self.asca = ASCAConfig.from_env()
        
        # Direct access properties
        self.asca_model_path = self.asca.model_path
        self.asca_language = self.asca.language
        self.asca_auto_detect_language = self.asca.auto_detect
        self.vncorenlp_path = self.asca.vncorenlp_path
        self.batch_size = int(os.getenv("BATCH_SIZE", "50"))
        self.max_records = int(os.getenv("MAX_RECORDS", "500"))


# Global settings instance
settings = Settings()
