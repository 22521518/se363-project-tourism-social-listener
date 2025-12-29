# YouTube Ingestion - Configuration
# Centralized configuration loading from environment variables

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

@dataclass(frozen=True)
class KafkaConfig():
    """Kafka configuration."""
    bootstrap_servers: str
    client_id: str
    topic: str
    group_id: str
    max_offsets_per_trigger: int
    processing_time: str
  
    
    @classmethod
    def from_env(cls) -> "KafkaConfig":
        """Load Kafka config from environment variables."""
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            topic=os.getenv("KAFKA_TOPIC", "youtube.comments"),
            client_id=os.getenv("KAFKA_CLIENT_ID", "traveling_type_extraction"),
            group_id=os.getenv("KAFKA_GROUP_ID", "traveling-type-extraction-group"),
            max_offsets_per_trigger=int(os.getenv("KAFKA_MAX_OFFSETS_PER_TRIGGER", "100")),
            processing_time=os.getenv("KAFKA_PROCESSING_TIME", "1 minute")
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




@dataclass
class ModelConfig:
    """Model configuration."""
    openai_api_key:str
    model_name: str
    
    @classmethod
    def from_env(cls) -> "ModelConfig":
        """Load model config from environment variables."""
        return cls(
            openai_api_key= os.getenv("OPENAI_API_KEY"),
            model_name=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        )


@dataclass
class ConsumerConfig:
    """Consumer configuration."""
    database: DatabaseConfig
    kafka: KafkaConfig
    model: ModelConfig
    
    @classmethod
    def from_env(cls) -> "ConsumerConfig":
        """Load consumer config from environment variables."""
        return cls(
            database= DatabaseConfig.from_env(),
            kafka=KafkaConfig.from_env(),
            model=ModelConfig.from_env()
        )

if __name__ == "__main__":
    config = ConsumerConfig.from_env()
    print(f"Database: {config.database}")
    print(f"Kafka: {config.kafka}")
    print(f"Model: {config.model}")

