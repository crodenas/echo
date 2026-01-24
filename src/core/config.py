"""Configuration module - DEPRECATED.

This module is maintained for backward compatibility.
New code should import from core.settings instead.

All configuration is now loaded from environment variables via the settings module.
See .env.example for required environment variables.
"""

from core.settings import get_settings

# Load settings from environment
_settings = get_settings()

# Export constants for backward compatibility
# These now come from environment variables instead of being hardcoded
QUEUE_1_URL: str = _settings.aws.queue_1_url
QUEUE_2_URL: str = _settings.aws.queue_2_url
QUEUE_1_ARN: str = _settings.aws.queue_1_arn
QUEUE_2_ARN: str = _settings.aws.queue_2_arn
EXECUTION_ROLE_ARN: str = _settings.aws.execution_role_arn

# Export settings instance for direct access
settings = _settings
