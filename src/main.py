"module"

import time
from datetime import datetime

from campaign import list_campaigns

# from scheduler import CampaignSchedulerFactory


def tick(name: str):
    "function"
    print(f"The time is: {datetime.now()} for {name}")


def main():
    "function"

    # Get Campaigns
    campaigns = list_campaigns()

    # For each campaign...
    for campaign in campaigns:
        print(f"Scheduling campaign: {campaign.id}:{campaign.name}")

    try:
        # Keep the main thread alive

        while True:
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        # Shut down the scheduler gracefully on exit
        print("Shutting down scheduler...")
        print("Scheduler shut down.")


if __name__ == "__main__":
    main()
