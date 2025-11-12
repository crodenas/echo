"""Module for loading sample campaigns into the database."""

import asyncio

import campaign as c
from models import Campaign


async def main():
    "main"
    # Create just one campaign with the specified schedules
    campaign_data = {
        "name": "SVT",
        "description": "Campaign with minute cycles and 5-second events per cycle",
        "campaign_frequency": "0 0 1 * *",
        "cycle_frequency": 5,
        "max_events": 5,
    }

    new_campaign = Campaign(
        id=None,
        name=campaign_data["name"],
        description=campaign_data["description"],
        campaign_schedule=campaign_data["campaign_frequency"],
        cycle_schedule=campaign_data["cycle_frequency"],
        max_events=campaign_data["max_events"],
    )
    await c.add_campaign(new_campaign)


if __name__ == "__main__":
    asyncio.run(main())
