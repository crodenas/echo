"""Scheduler service for managing campaign schedulers."""

from datetime import datetime
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler

from campaign import list_campaigns
from scheduler import CampaignSchedulerFactory


def tick_job(name: str) -> None:
    """
    Simple job that logs the current time.
    This function needs to be at module level to be properly serialized.

    Args:
        name: The name to include in the log message
    """
    print(f"The time is: {datetime.now()} for {name}")


class SchedulerService:
    """Service for managing campaign schedulers."""

    _instance = None
    _schedulers: List[BackgroundScheduler] = []

    def __new__(cls):
        """Create a singleton instance."""
        if cls._instance is None:
            cls._instance = super(SchedulerService, cls).__new__(cls)
        return cls._instance

    def _create_job_config(self, schedule, _campaign=None):
        """
        Create job configuration based on schedule type.

        Args:
            schedule: The schedule configuration (CronSchedule, IntervalSchedule, OneTimeSchedule)
            _campaign: (Optional) The campaign the job belongs to, for potential future use

        Returns:
            dict: Configuration for scheduler.add_job
        """
        from models import CronSchedule, IntervalSchedule, OneTimeSchedule

        if isinstance(schedule, CronSchedule):
            # Create a cron trigger configuration
            config = {
                "trigger": "cron",
            }
            if schedule.minute is not None:
                config["minute"] = schedule.minute
            if schedule.hour is not None:
                config["hour"] = schedule.hour
            if schedule.day is not None:
                config["day"] = schedule.day
            if schedule.month is not None:
                config["month"] = schedule.month
            if schedule.day_of_week is not None:
                config["day_of_week"] = schedule.day_of_week
            return config

        elif isinstance(schedule, IntervalSchedule):
            # Create an interval trigger configuration
            config = {
                "trigger": "interval",
            }
            if schedule.weeks is not None:
                config["weeks"] = schedule.weeks
            if schedule.days is not None:
                config["days"] = schedule.days
            if schedule.hours is not None:
                config["hours"] = schedule.hours
            if schedule.minutes is not None:
                config["minutes"] = schedule.minutes
            if schedule.seconds is not None:
                config["seconds"] = schedule.seconds
            return config

        elif isinstance(schedule, OneTimeSchedule):
            # Create a date trigger configuration
            return {"trigger": "date", "run_date": schedule.run_date}

        # Default to a simple hourly job if schedule type is unknown
        return {"trigger": "cron", "minute": "0"}

    @property
    def schedulers(self) -> List[BackgroundScheduler]:
        """Get the list of active schedulers."""
        return self._schedulers

    # Removed the tick instance method in favor of the module-level tick_job function

    def start(self) -> None:
        """Start all campaign schedulers."""
        # Clear existing schedulers
        self._schedulers = []

        scheduler_factory = CampaignSchedulerFactory()

        # Get Campaigns
        campaigns = list_campaigns()

        # For each campaign, start each scheduler
        for campaign in campaigns:
            print(f"Scheduling campaign: {campaign.id}:{campaign.name}")
            scheduler = scheduler_factory.create_scheduler(campaign)
            self._schedulers.append(scheduler)
            # Add job based on cycle schedule type
            if campaign.cycle_schedule:
                job_config = self._create_job_config(campaign.cycle_schedule, campaign)
                scheduler.add_job(
                    tick_job,
                    **job_config,
                    args=[f"Campaign {campaign.name}"],
                    id=f"tick_{campaign.id}",
                    replace_existing=True,
                )
            scheduler.start()
        print(f"Started {len(self._schedulers)} schedulers")

    def stop(self) -> None:
        """Stop all active schedulers."""
        print("Shutting down schedulers...")
        for scheduler in self._schedulers:
            scheduler.shutdown()
        self._schedulers = []
        print("Schedulers shut down.")
