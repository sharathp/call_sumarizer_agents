"""
Centralized configuration management.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class TranscriptionProvider(str, Enum):
    """Supported transcription providers."""
    DEEPGRAM = "deepgram"
    WHISPER = "whisper"


@dataclass
class APIConfig:
    """API configuration container."""
    openai_api_key: Optional[str] = None
    deepgram_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    langsmith_api_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create config from environment variables."""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            deepgram_api_key=os.getenv("DEEPGRAM_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            langsmith_api_key=os.getenv("LANGCHAIN_API_KEY")
        )
    
    def validate(self, require_transcription: bool = True) -> list[str]:
        """
        Validate configuration and return list of missing requirements.
        
        Args:
            require_transcription: Whether transcription API is required
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # At least one LLM provider is required
        if not self.openai_api_key and not self.anthropic_api_key:
            errors.append("At least one LLM API key required (OpenAI or Anthropic)")
        
        # Transcription provider check
        if require_transcription and not self.deepgram_api_key:
            errors.append("Deepgram API key required for transcription with diarization")
        
        return errors
    
    def get_llm_provider(self) -> Optional[ModelProvider]:
        """Get the available LLM provider."""
        if self.openai_api_key:
            return ModelProvider.OPENAI
        if self.anthropic_api_key:
            return ModelProvider.ANTHROPIC
        return None


@dataclass
class ModelConfig:
    """Model configuration settings."""
    # LLM settings
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.3
    llm_provider: ModelProvider = ModelProvider.OPENAI
    
    # Transcription settings
    transcription_model: str = "nova-2"
    transcription_provider: TranscriptionProvider = TranscriptionProvider.DEEPGRAM
    enable_diarization: bool = True
    
    # Retry settings
    max_retries: int = 2
    retry_delay: float = 1.0


@dataclass
class AppConfig:
    """Application-wide configuration."""
    api: APIConfig
    model: ModelConfig
    
    # Logging
    log_level: str = "INFO"
    enable_langsmith: bool = False
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create complete configuration from environment."""
        api_config = APIConfig.from_env()
        
        # Enable LangSmith if API key is present
        enable_langsmith = bool(api_config.langsmith_api_key)
        if enable_langsmith:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = api_config.langsmith_api_key
        
        return cls(
            api=api_config,
            model=ModelConfig(),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            enable_langsmith=enable_langsmith
        )


# Global configuration instance
config = AppConfig.from_env()