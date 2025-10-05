"""Scheduler service for managing campaign schedulers."""

from datetime import datetime
from typing import List, Dict

from apscheduler.schedulers.background import BackgroundScheduler

from campaign import list_campaigns
from scheduler import CampaignSchedulerFactory

# Dictionary to track escalation event counts
# Don't use global keyword, just use the module-level variable
event_counters: Dict[str, int] = {}


def tick_job(name: str) -> None:
    """
    Simple job that logs the current time.
    This function needs to be at module level to be properly serialized.

    Args:
        name: The name to include in the log message
    """
    print(f"The time is: {datetime.now()} for {name}")


def escalation_job(name: str, max_events: int) -> None:
    """
    Job for escalation events with a counter to limit the number of executions.

    Args:
        name: The name to include in the log message
        max_events: Maximum number of events to trigger
    """
    # Use the module-level variable directly
    job_key = f"escalation_{name}"

    # Initialize counter if not exists
    if job_key not in event_counters:
        event_counters[job_key] = 0

    # Increment counter
    event_counters[job_key] += 1
    current_count = event_counters[job_key]

    if current_count <= max_events:
        print(
            f"ESCALATION EVENT {current_count}/{max_events} at {datetime.now()} for {name}"
        )
        # Log when we've reached the maximum number of events
        if current_count == max_events:
            print(
                f"Escalation limit reached for {name}. No more events will be triggered."
            )


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

    def start(self) -> None:
        """Start all campaign schedulers."""
        # Clear existing schedulers
        self._schedulers = []

        # Reset the module-level event counters
        event_counters.clear()

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
                scheduler.add_job(
                    tick_job,
                    **campaign.cycle_schedule.create_job_config(),
                    args=[f"Campaign {campaign.name}"],
                    id=f"tick_{campaign.id}",
                    replace_existing=True,
                )

            # Add job based on escalation schedule
            if campaign.escalation_schedule:
                scheduler.add_job(
                    escalation_job,
                    **campaign.escalation_schedule.create_job_config(),
                    args=[f"Campaign {campaign.name}", 5],  # Limit to 5 events
                    id=f"escalation_{campaign.id}",
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

        # Reset the module-level event counters
        event_counters.clear()

        print("Schedulers shut down.")
