"module"

from typing import Optional

from pydantic import BaseModel, field_validator

from data import db
from models import Resource


class NotificationTemplates(BaseModel):
    """Templates for different notification types."""

    email: str  # Email template use to send email notifications
    slack: Optional[str] = None  # Slack template (optional)
    teams: Optional[str] = None  # Microsoft Teams template (optional)

    @classmethod
    def email_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Email template cannot be empty")
        return v


class RunConfig(BaseModel):
    """Run config for a notification run."""


class Cycle(BaseModel):
    """Cycle config for a notification cycle."""


class Campaign(BaseModel):
    """Campaign config for a notification campaign."""

    campaign_id: int  # Unique identifier for the campaign from the DB
    name: str
    description: Optional[str] = None  # Optional description of the campaign
    data_source: str
    templates: dict  # Dictionary of templates for different notification types

    cycle_rrule: str  # Rule defining the cycle schedule


def get_campaign_objects() -> list[Resource]:
    """Get all campaign objects from the database."""
    # Load campaign objects from JSON file
    campaign_data = db.read_json_db("data/Campaign1.json")
    return [Resource(**obj) for obj in campaign_data]


def get_campaigns() -> list[Campaign]:
    """Get all campaigns from the database."""
    # Load campaigns from JSON file
    campaign_data = db.read_json_db("data/Campaigns.json")
    return [Campaign(**obj) for obj in campaign_data]
