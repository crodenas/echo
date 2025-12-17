"""Core business logic and domain models for Echo.

This package contains:
- Domain models (Pydantic)
- Configuration
- Scheduler integration
- Lifecycle management
"""

from core.models import Campaign, CampaignCreate, CampaignUpdate

__all__ = [
    "Campaign",
    "CampaignCreate",
    "CampaignUpdate",
]
