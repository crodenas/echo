"module"

from dataclasses import dataclass


@dataclass
class CampaignCreate:
    """Model for creating a new campaign (excludes id)."""

    name: str
    campaign_schedule: str  # AWS crontab schedule
    cycle_schedule: str  # AWS crontab schedule
    description: str | None = None
    max_events: int | None = None


@dataclass
class CampaignUpdate:
    """Model for updating an existing campaign (excludes id)."""

    name: str
    campaign_frequency: str  # AWS crontab schedule
    cycle_schedule: str  # AWS crontab schedule
    description: str | None = None
    max_events: int | None = None


@dataclass
class Campaign:
    """Full campaign model including id."""

    name: str
    campaign_schedule: str  # AWS crontab schedule
    cycle_schedule: str  # AWS crontab schedule
    description: str | None = None
    max_events: int | None = None
    id: int | None = None


@dataclass
class Employee:
    "class"

    first_name: str
    last_name: str
    global_id: int
    system_id: str
    internet_email_address: str
    job_title: str
    supervisor_system_id: str | None
