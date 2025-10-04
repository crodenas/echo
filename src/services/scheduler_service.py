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
            scheduler.add_job(
                tick_job,
                trigger="cron",
                minute="*",
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
