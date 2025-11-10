"module"

from dataclasses import dataclass


@dataclass
class Campaign:
    "class"

    name: str
    campaign_frequency: int  # in months
    cycle_frequency: int  # in days
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
