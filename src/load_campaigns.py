"""Module for loading sample campaigns into the database."""

import campaign as c
from models import Campaign, CronSchedule


def main():
    # Define weekly schedule (runs every Monday at 9:00 AM)
    weekly_schedule = CronSchedule(
        minute="0", hour="9", day="*", month="*", day_of_week="0"  # Monday
    )

    campaigns = [
        {
            "name": "SVT",
            "description": "Swedish Public Service Television",
            "cycle_schedule": weekly_schedule,
            "escalation_schedule": "Hourly",
        },
        {
            "name": "CVT",
            "description": "Czech Public Service Television",
            "cycle_schedule": weekly_schedule,
            "escalation_schedule": "Hourly",
        },
    ]

    for campaign in campaigns:
        new_campaign = Campaign(
            id=None,
            name=campaign["name"],
            description=campaign["description"],
            cycle_schedule=campaign["cycle_schedule"],
            escalation_schedule=campaign["escalation_schedule"],
        )
        c.add_campaign(new_campaign)


if __name__ == "__main__":
    main()
