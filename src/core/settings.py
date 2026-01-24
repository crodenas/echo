"""Configuration management using environment variables.

This module provides environment-based configuration for the ECHO application,
replacing hardcoded values with secure, externalized configuration.
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSSettings(BaseSettings):
    """AWS-specific configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="AWS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # SQS Queue Configuration
    queue_1_url: str = Field(
        ...,
        description="SQS Queue 1 URL for campaign start triggers",
    )
    queue_1_arn: str = Field(
        ...,
        description="SQS Queue 1 ARN for campaign start triggers",
    )
    queue_2_url: str = Field(
        ...,
        description="SQS Queue 2 URL for cycle execution",
    )
    queue_2_arn: str = Field(
        ...,
        description="SQS Queue 2 ARN for cycle execution",
    )

    # IAM Configuration
    execution_role_arn: str = Field(
        ...,
        description="IAM role ARN for EventBridge Scheduler to invoke SQS targets",
    )

    # Regional Configuration
    region: str = Field(
        default="us-east-2",
        description="AWS region for all services",
    )

    # Operation Timeouts (in seconds)
    scheduler_operation_timeout: int = Field(
        default=30,
        description="Timeout for EventBridge Scheduler operations",
        ge=1,
        le=300,
    )
    sqs_operation_timeout: int = Field(
        default=10,
        description="Timeout for SQS operations",
        ge=1,
        le=60,
    )

    # Retry Configuration
    max_retry_attempts: int = Field(
        default=3,
        description="Maximum number of retry attempts for AWS operations",
        ge=1,
        le=10,
    )
    retry_min_wait: int = Field(
        default=1,
        description="Minimum wait time between retries in seconds",
        ge=1,
        le=60,
    )
    retry_max_wait: int = Field(
        default=10,
        description="Maximum wait time between retries in seconds",
        ge=1,
        le=300,
    )

    @field_validator("queue_1_url", "queue_2_url")
    @classmethod
    def validate_queue_url(cls, v: str) -> str:
        """Validate SQS queue URL format."""
        if not v.startswith("https://sqs."):
            raise ValueError("Queue URL must start with 'https://sqs.'")
        return v

    @field_validator("queue_1_arn", "queue_2_arn", "execution_role_arn")
    @classmethod
    def validate_arn(cls, v: str) -> str:
        """Validate AWS ARN format."""
        if not v.startswith("arn:aws:"):
            raise ValueError("ARN must start with 'arn:aws:'")
        return v


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    url: str = Field(
        default="sqlite:///./src/data/echo.db",
        description="Database connection URL",
    )

    @property
    def path(self) -> Path | None:
        """Extract file path from SQLite URL."""
        if self.url.startswith("sqlite:///"):
            # Remove 'sqlite:///' prefix and return Path
            return Path(self.url.replace("sqlite:///", ""))
        return None


class AppSettings(BaseSettings):
    """Main application settings container."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    skip_aws_validation: bool = Field(
        default=False,
        description="Skip AWS connectivity validation on startup (for local development)",
    )

    # Nested Settings
    aws: AWSSettings = Field(default_factory=AWSSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level value."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper


# Global settings instance - initialized on first import
_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    """Get or create the global settings instance.

    Returns:
        AppSettings: The application settings instance

    Raises:
        ValueError: If required environment variables are missing
    """
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings


# Convenience function to reload settings (useful for testing)
def reload_settings() -> AppSettings:
    """Force reload of settings from environment.

    Returns:
        AppSettings: The freshly loaded application settings
    """
    global _settings
    _settings = AppSettings()
    return _settings
