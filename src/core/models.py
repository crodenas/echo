"module"

from typing import Optional

from pydantic import BaseModel


class CampaignCreate(BaseModel):
    """Model for creating a new campaign (excludes id)."""

    name: str
    campaign_schedule: str  # AWS crontab schedule
    cycle_schedule: str  # AWS crontab schedule
    description: str
    max_events: int
    conn_string: Optional[str] = None


class CampaignUpdate(BaseModel):
    """Model for updating an existing campaign (excludes id)."""

    name: str
    campaign_schedule: str  # AWS crontab schedule
    cycle_schedule: str  # AWS crontab schedule
    description: str
    max_events: int
    conn_string: Optional[str] = None


class Campaign(BaseModel):
    """Full campaign model including id."""

    name: str
    campaign_schedule: str  # AWS crontab schedule
    cycle_schedule: str  # AWS crontab schedule
    description: Optional[str]
    max_events: Optional[int]
    id: Optional[int] = None
    conn_string: Optional[str] = None  # Database connection string


class Employee(BaseModel):
    """Employee model."""

    first_name: str
    last_name: str
    global_id: int
    system_id: str
    internet_email_address: str
    job_title: str
    supervisor_system_id: Optional[str] = None
