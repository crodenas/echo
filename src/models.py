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
class OneTimeSchedule:
    "class"

    run_date: str  # ISO 8601 format


@dataclass
class Campaign:
    "class"

    id: int | None
    name: str
    description: str | None
    cycle_schedule: CronSchedule | IntervalSchedule | OneTimeSchedule | None
    escalation_schedule: CronSchedule | IntervalSchedule | OneTimeSchedule | None


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
