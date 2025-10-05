"""Module for loading sample campaigns into the database."""

import campaign as c
from models import Campaign, IntervalSchedule


def main():
    # Define a minute interval schedule (runs every minute)
    minute_schedule = IntervalSchedule(
        weeks=None, days=None, hours=None, minutes=1, seconds=None
    )

    # Define a 5-second interval schedule for escalation with only 5 events
    five_second_schedule = IntervalSchedule(
        weeks=None, days=None, hours=None, minutes=None, seconds=5
    )

    # Create just one campaign with the specified schedules
    campaign_data = {
        "name": "Fast Escalation Demo",
        "description": "Campaign with minute cycle and 5-second escalation (limited to 5 events)",
        "cycle_schedule": minute_schedule,
        "escalation_schedule": five_second_schedule,
    }

    new_campaign = Campaign(
        id=None,
        name=campaign_data["name"],
        description=campaign_data["description"],
        cycle_schedule=campaign_data["cycle_schedule"],
        escalation_schedule=campaign_data["escalation_schedule"],
    )
    c.add_campaign(new_campaign)


if __name__ == "__main__":
    main()
