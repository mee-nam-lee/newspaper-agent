"""Configuration module for the Newspaper Agent."""

import logging
import os

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentModel(BaseModel):
    """Agent model settings."""

    name: str = Field(default="newspaper_agent")
    model: str = Field(default="gemini-3.5-flash")


class Config(BaseSettings):
    """Configuration settings for the Newspaper Agent."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../.env"
        ),
        env_prefix="",
        case_sensitive=True,
        extra="ignore",
    )

    agent_settings: AgentModel = Field(default=AgentModel())
    app_name: str = "newspaper_agent_app"

    # Cloud & Auth Config
    GOOGLE_CLOUD_PROJECT: str = Field(
        default="", description="Google Cloud Project ID"
    )
    GOOGLE_CLOUD_LOCATION: str = Field(default="global")
    GOOGLE_GENAI_USE_VERTEXAI: str = Field(default="1")
    GOOGLE_GENAI_LOCATION: str = Field(default="global")

    # Storage Configuration
    PUBLIC_ARTIFACT_BUCKET: str = Field(
        description="GCS Bucket for publishing public artifacts (HTML reports, images).",
    )

    @property
    def full_model_name(self) -> str:
        """Constructs the full model resource name."""
        return f"projects/{self.GOOGLE_CLOUD_PROJECT}/locations/{self.GOOGLE_GENAI_LOCATION}/publishers/google/models/{self.agent_settings.model}"


config = Config()
