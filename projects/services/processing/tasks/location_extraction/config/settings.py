"""
Configuration settings for the Location Extraction module.
Uses Pydantic Settings for environment variable management.
"""

from enum import Enum
from typing import Optional
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GOOGLE = "google"
    TOGETHERAI = "togetherai"


class Settings(BaseSettings):
    """
    Location Extraction module settings.
    
    Environment variables are loaded from .env file or system environment.
    """
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Provider Selection
    llm_provider: LLMProvider = Field(
        default=LLMProvider.GOOGLE,
        description="LLM provider to use (google or togetherai)"
    )
    
    # API Keys
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google Gemini API key"
    )
    together_api_key: Optional[str] = Field(
        default=None,
        description="TogetherAI API key"
    )
    
    # Model Configuration
    llm_model_name: str = Field(
        default="gemini-2.5-flash-lite",
        description="LLM model name to use"
    )
    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="LLM temperature (0.0 - 1.0)"
    )
    llm_max_tokens: int = Field(
        default=1024,
        ge=1,
        description="Maximum tokens for LLM response"
    )
    
    # Extraction Settings
    max_locations: int = Field(
        default=10,
        ge=1,
        description="Maximum number of locations to extract"
    )
    min_confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    description="Minimum confidence threshold for locations"
    )

    # Database Configuration
    db_host: str = Field("localhost", description="Database host")
    db_port: int = Field(5432, description="Database port")
    db_user: str = Field("airflow", description="Database user")
    db_password: str = Field("airflow", description="Database password")
    db_name: str = Field("airflow", description="Database name")

    # Kafka Configuration
    kafka_bootstrap_servers: str = Field("localhost:9092", description="Kafka bootstrap servers")
    kafka_topic_location_input: str = Field("location-extraction-input", description="Input topic for location extraction")
    kafka_topic_location_output: str = Field("location-extraction-output", description="Output topic for location extraction")
    kafka_consumer_group: str = Field("location-extraction-consumer", description="Consumer group ID")
    
    def get_api_key(self) -> str:
        """Get the API key for the configured provider."""
        if self.llm_provider == LLMProvider.GOOGLE:
            if not self.google_api_key:
                raise ValueError("GOOGLE_API_KEY is required when using Google provider")
            return self.google_api_key
        elif self.llm_provider == LLMProvider.TOGETHERAI:
            if not self.together_api_key:
                raise ValueError("TOGETHER_API_KEY is required when using TogetherAI provider")
            return self.together_api_key
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    

    def get_default_model_for_provider(self) -> str:
        """Get the default model name for the configured provider."""
        defaults = {
            LLMProvider.GOOGLE: "gemini-2.5-flash-lite",
            LLMProvider.TOGETHERAI: "meta-llama/Llama-3-70b-chat-hf"
        }
        return defaults.get(self.llm_provider, self.llm_model_name)


class DatabaseConfig:
    """Database configuration."""
    
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        
    @property
    def connection_string(self) -> str:
        """Get SQLAlchemy connection string."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create config from environment variables."""
        # We use the global settings instance to access env vars if we added them there,
        # but standard way in this project seems to be direct env var access or mixing.
        # Let's add DB fields to Settings class first or just access os.environ in this method 
        # to match intention/config.py style if that's what it did.
        # Actually, let's extend the Settings class to include DB params.
        # But for now, let's just stick to the pattern.
        
        # Since I'm editing the file, I should probably add the fields to Settings class
        # and use settings instance.
        s = settings
        return cls(
            host=s.db_host,
            port=s.db_port,
            user=s.db_user,
            password=s.db_password,
            database=s.db_name
        )


# Global settings instance
settings = Settings()


class KafkaConfig:
    """Kafka configuration helper."""
    
    def __init__(self, bootstrap_servers: str, input_topic: str, output_topic: str, consumer_group: str):
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.consumer_group = consumer_group
    
    @classmethod
    def from_env(cls) -> "KafkaConfig":
        """Create config from environment variables via Settings."""
        s = settings
        return cls(
            bootstrap_servers=s.kafka_bootstrap_servers,
            input_topic=s.kafka_topic_location_input,
            output_topic=s.kafka_topic_location_output,
            consumer_group=s.kafka_consumer_group
        )
