"""Scheduler service for managing campaign schedulers."""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError

from campaign import list_campaigns
from scheduler import CampaignSchedulerFactory

# Dictionary to track escalation event counts and store scheduler references
# Don't use global keyword, just use the module-level variable
event_counters: Dict[str, int] = {}
scheduler_registry: Dict[str, Any] = {}


def tick_job(name: str, campaign_id: str) -> None:
    """
    Job that logs the current time and triggers escalation scheduling.
    This function needs to be at module level to be properly serialized.

    When this job runs on each cycle, it creates a new sequence of escalation events
    by resetting the counter and scheduling new escalation jobs.

    Args:
        name: The name to include in the log message
        campaign_id: The ID of the campaign
    """
    current_time = datetime.now()
    print(f"The time is: {current_time} for {name}")

    # Create a key for the escalation counter
    full_name = f"Campaign {name}"
    job_key = f"escalation_{full_name}"

    # Reset the counter for the new cycle
    if job_key in event_counters:
        previous_count = event_counters[job_key]
        print(f"Resetting escalation counter for {name} from {previous_count} to 0")
    else:
        print(f"Initializing escalation counter for {name}")

    event_counters[job_key] = 0

    # Get the scheduler instance from the registry
    scheduler_key = f"scheduler_{campaign_id}"
    if scheduler_key in scheduler_registry:
        scheduler = scheduler_registry[scheduler_key]

        # Create a new escalation job for this cycle
        job_id = f"escalation_{campaign_id}"

        # First remove any existing job
        try:
            scheduler.remove_job(job_id)
        except JobLookupError:
            # Job might not exist, that's okay
            pass

        # Create a new escalation job with regular intervals
        # Each cycle will create a new series of escalations
        scheduler.add_job(
            escalation_job,
            trigger="interval",
            minutes=5,  # Run escalation every 5 minutes
            start_date=current_time,
            end_date=current_time + timedelta(hours=1),  # Run for 1 hour
            args=[f"Campaign {name}", 5],  # Limit to 5 events
            id=job_id,
            replace_existing=True,
        )
        print(
            f"New escalation sequence scheduled for {name} starting at {current_time}"
        )
    else:
        print(f"Warning: No scheduler found for campaign {campaign_id} in the registry")


def escalation_job(name: str, max_events: int) -> None:
    """
    Job for escalation events with a counter to limit the number of executions.
    This function is scheduled by the tick_job and runs at regular intervals
    for a limited period after each cycle starts.

    Args:
        name: The name to include in the log message
        max_events: Maximum number of events to trigger
    """
    # Use the same key format as in tick_job to track escalation events
    job_key = f"escalation_{name}"

    # Initialize counter if not exists (although tick_job should have done this already)
    if job_key not in event_counters:
        event_counters[job_key] = 0

    # Increment counter
    event_counters[job_key] += 1
    current_count = event_counters[job_key]

    # Process based on current count
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

        # Reset the module-level event counters and scheduler registry
        event_counters.clear()
        scheduler_registry.clear()

        scheduler_factory = CampaignSchedulerFactory()

        # Get Campaigns
        campaigns = list_campaigns()

        # For each campaign, start each scheduler
        for campaign in campaigns:
            print(f"Scheduling campaign: {campaign.id}:{campaign.name}")
            scheduler = scheduler_factory.create_scheduler(campaign)
            self._schedulers.append(scheduler)

            # Register the scheduler for use by tick_job
            scheduler_key = f"scheduler_{campaign.id}"
            scheduler_registry[scheduler_key] = scheduler

            # Add job based on cycle schedule type
            if campaign.cycle_schedule:
                scheduler.add_job(
                    tick_job,
                    **campaign.cycle_schedule.create_job_config(),
                    args=[f"Campaign {campaign.name}", campaign.id],
                    id=f"tick_{campaign.id}",
                    replace_existing=True,
                )  # Escalation jobs will be dynamically created by the tick_job
            # If a campaign has an escalation_schedule configured, it will be used as a reference
            # but the actual scheduling is handled by the tick_job

            scheduler.start()
        print(f"Started {len(self._schedulers)} schedulers")

    def stop(self) -> None:
        """Stop all active schedulers."""
        print("Shutting down schedulers...")
        for scheduler in self._schedulers:
            scheduler.shutdown()
        self._schedulers = []

        # Reset the module-level event counters and scheduler registry
        event_counters.clear()
        scheduler_registry.clear()

        print("Schedulers shut down.")
