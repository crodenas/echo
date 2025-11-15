"""Module for loading sample campaigns into the database."""

import asyncio
from models import Campaign
import scheduler


async def main():
    "main"
    # Create just one campaign with the specified schedules
    campaign_data = {
        "name": "SVT",
        "description": "Campaign with 5 minute cycles and 1 minute cycle event schedule",
        "campaign_schedule": "cron(*/5 * * * ? *)",
        "cycle_schedule": "*/1 * * * ? *",
        "max_events": 5,
    }

    new_campaign = Campaign(
        id=None,
        name=campaign_data["name"],
        description=campaign_data["description"],
        campaign_schedule=campaign_data["campaign_schedule"],
        cycle_schedule=campaign_data["cycle_schedule"],
        max_events=campaign_data["max_events"],
    )

    result = await scheduler.create_cycle_schedules(new_campaign)

    print("Cycle schedule parameters:")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
