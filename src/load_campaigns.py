"module"

import campaign as c
from models import Campaign


def main():
    campaigns = [
        {
            "name": "SVT",
            "description": "Swedish Public Service Television",
            "cycle_schedule": "Weekly",
            "escalation_schedule": "Hourly",
        },
        {
            "name": "CVT",
            "description": "Czech Public Service Television",
            "cycle_schedule": "Weekly",
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
