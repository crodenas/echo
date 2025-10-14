"""Scheduler service for managing campaign schedulers."""

from datetime import datetime
from typing import List, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError

from campaign import list_campaigns, get_campaign
from scheduler import CampaignSchedulerFactory

# Dictionary to track escalation event counts and store scheduler references
# Don't use global keyword, just use the module-level variable
event_counters: Dict[str, int] = {}
scheduler_registry: Dict[str, Any] = {}


def start_new_cycle(name: str, campaign_id: str) -> None:
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

    # Get the campaign from the database to access cycle_schedule
    campaign = get_campaign(int(campaign_id))
    if not campaign or not campaign.cycle_schedule:
        print(f"Warning: No cycle schedule found for campaign {campaign_id}")
        return

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

        # Create job configuration from the campaign's cycle_schedule
        job_config = campaign.cycle_schedule.create_job_config()
        job_config["start_date"] = current_time

        # No end_date needed - the job will remove itself after max_events

        # Use max_events from campaign or default to 5 if not specified
        max_events = campaign.max_events if campaign.max_events is not None else 5

        # Execute the first cycle event immediately (no delay)
        cycle_event(name, max_events, campaign_id, current_time)

        # If there are more events to schedule (max_events > 1), schedule the remaining ones
        if max_events > 1:
            # Create a new escalation job using the cycle schedule configuration
            scheduler.add_job(
                cycle_event,
                **job_config,
                args=[name, max_events, campaign_id, current_time],
                id=job_id,
                replace_existing=True,
            )
            print(
                f"New escalation sequence scheduled for {name} starting at {current_time} using cycle schedule"
            )
        else:
            print(
                f"Single event cycle for {name} completed immediately at {current_time}"
            )
    else:
        print(f"Warning: No scheduler found for campaign {campaign_id} in the registry")


def cycle_event(
    name: str, max_events: int, campaign_id: str, cycle_start_date: datetime
) -> None:
    """
    Job for cycle events with a counter to limit the number of executions.
    The first event is called immediately by start_new_cycle, then subsequent
    events are scheduled at regular intervals until reaching max_events.

    Args:
        name: The campaign name
        max_events: Maximum number of events to trigger
        campaign_id: The ID of the campaign (used to find the correct scheduler)
        cycle_start_date: When this cycle started
    """
    # Use the same key format as in start_new_cycle to track cycle events
    job_key = f"Campaign {name}"

    # Initialize counter if not exists (although start_new_cycle should have done this already)
    if job_key not in event_counters:
        event_counters[job_key] = 0

    # Increment counter
    event_counters[job_key] += 1
    current_count = event_counters[job_key]

    # Process based on current count
    if current_count <= max_events:
        print(
            f"CYCLE EVENT - Campaign ID: {campaign_id}, Name: {name}, "
            f"Cycle Start: {cycle_start_date.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"Event: {current_count}/{max_events}, "
            f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Remove the job when we've reached the maximum number of events
        if current_count == max_events:
            print(
                f"CYCLE COMPLETE - Campaign ID: {campaign_id}, Name: {name}, "
                f"All {max_events} events completed. Removing cycle job."
            )

            # Get the scheduler and remove the job
            scheduler_key = f"scheduler_{campaign_id}"
            if scheduler_key in scheduler_registry:
                scheduler = scheduler_registry[scheduler_key]
                job_id = f"escalation_{campaign_id}"
                try:
                    scheduler.remove_job(job_id)
                    print(
                        f"Successfully removed cycle job {job_id} for campaign {campaign_id}"
                    )
                except JobLookupError:
                    print(f"Warning: Cycle job {job_id} was already removed")
            else:
                print(f"Warning: No scheduler found for campaign {campaign_id}")


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
            if campaign.campaign_schedule:
                scheduler.add_job(
                    start_new_cycle,
                    **campaign.campaign_schedule.create_job_config(),
                    args=[f"Campaign {campaign.name}", campaign.id],
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

        # Reset the module-level event counters and scheduler registry
        event_counters.clear()
        scheduler_registry.clear()

        print("Schedulers shut down.")
