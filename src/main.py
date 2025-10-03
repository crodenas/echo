"module"

import time
from datetime import datetime

from campaign import list_campaigns
from scheduler import CampaignSchedulerFactory


def tick(name: str):
    "function"
    print(f"The time is: {datetime.now()} for {name}")


def main():
    "function"

    scheduler_factory = CampaignSchedulerFactory()
    schedulers = []

    # Get Campaigns
    campaigns = list_campaigns()

    # For each campaign, start each scheduler
    for campaign in campaigns:
        print(f"Scheduling campaign: {campaign.id}:{campaign.name}")
        scheduler = scheduler_factory.create_scheduler(campaign)
        schedulers.append(scheduler)
        scheduler.add_job(
            tick,
            trigger="cron",
            minute="*",
            args=[f"Campaign {campaign.name}"],
            id=f"tick_{campaign.id}",
            replace_existing=True,
        )
        scheduler.start()
    try:
        # Keep the main thread alive

        while True:
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        # Shut down the scheduler gracefully on exit
        print("Shutting down schedulers...")
        for scheduler in schedulers:
            scheduler.shutdown()
        print("Scheduler shut down.")


if __name__ == "__main__":
    main()
