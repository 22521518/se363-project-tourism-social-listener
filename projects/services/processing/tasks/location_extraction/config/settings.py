"""
Configuration settings for the Location Extraction module.
Uses Pydantic Settings for environment variable management.
"""

from enum import Enum
from typing import Optional
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
        env_file=".env",
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


# Global settings instance
settings = Settings()
