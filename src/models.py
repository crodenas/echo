"module"

from dataclasses import dataclass


@dataclass
class CronSchedule:
    "class"

    minute: str | None
    hour: str | None
    day: str | None
    month: str | None
    day_of_week: str | None


@dataclass
class IntervalSchedule:
    "class"

    weeks: int | None
    days: int | None
    hours: int | None
    minutes: int | None
    seconds: int | None


@dataclass
class Campaign:
    "class"

    id: int | None
    name: str
    description: str | None
    cycle_schedule: CronSchedule | None
    escalation_schedule: str | None


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
