"module"

from abc import ABC, abstractmethod
from dataclasses import dataclass


class Schedule(ABC):
    """Base abstract class for all schedule types."""

    @abstractmethod
    def create_job_config(self) -> dict:
        """Create configuration for scheduler.add_job method."""


@dataclass
class CronSchedule(Schedule):
    "class"

    minute: str | None
    hour: str | None
    day: str | None
    month: str | None
    day_of_week: str | None

    def create_job_config(self) -> dict:
        """Create a cron trigger configuration."""
        config = {
            "trigger": "cron",
        }
        if self.minute is not None:
            config["minute"] = self.minute
        if self.hour is not None:
            config["hour"] = self.hour
        if self.day is not None:
            config["day"] = self.day
        if self.month is not None:
            config["month"] = self.month
        if self.day_of_week is not None:
            config["day_of_week"] = self.day_of_week
        return config


@dataclass
class IntervalSchedule(Schedule):
    "class"

    weeks: int | None
    days: int | None
    hours: int | None
    minutes: int | None
    seconds: int | None

    def create_job_config(self) -> dict:
        """Create an interval trigger configuration."""
        config = {
            "trigger": "interval",
        }
        if self.weeks is not None:
            config["weeks"] = self.weeks
        if self.days is not None:
            config["days"] = self.days
        if self.hours is not None:
            config["hours"] = self.hours
        if self.minutes is not None:
            config["minutes"] = self.minutes
        if self.seconds is not None:
            config["seconds"] = self.seconds
        return config


@dataclass
class OneTimeSchedule(Schedule):
    "class"

    run_date: str  # ISO 8601 format

    def create_job_config(self) -> dict:
        """Create a date trigger configuration."""
        return {"trigger": "date", "run_date": self.run_date}


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
