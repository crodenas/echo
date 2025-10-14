"""Module for loading sample campaigns into the database."""

import campaign as c
from models import Campaign, IntervalSchedule


def main():
    "main"
    # Define a minute interval schedule (runs every minute)
    minute_schedule = IntervalSchedule(
        weeks=None,
        days=None,
        hours=None,
        minutes=1,
        seconds=None,
    )

    # Define a 5-second interval schedule for escalation with only 5 events
    five_second_schedule = IntervalSchedule(
        weeks=None,
        days=None,
        hours=None,
        minutes=None,
        seconds=5,
    )

    # Create just one campaign with the specified schedules
    campaign_data = {
        "name": "SVT",
        "description": "Campaign with minute cycles and 5-second events per cycle",
        "campaign_schedule": minute_schedule,
        "cycle_schedule": five_second_schedule,
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
    c.add_campaign(new_campaign)


if __name__ == "__main__":
    main()
