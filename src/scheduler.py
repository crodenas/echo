"""
Scheduler utilities for creating one-time schedules.
"""

import json
from datetime import datetime, timezone

import config
from aws import scheduler
from models import Campaign

TARGET_ARN: str = config.TARGET_ARN
EXECUTION_ROLE_ARN: str = config.EXECUTION_ROLE_ARN


def create_schedule_group(campaign: Campaign) -> None:
    "function"
    group_name = f"campaign_{campaign.id}_group"
    tags = [{"Key": "CampaignID", "Value": str(campaign.id)}]

    # Create the schedule group
    scheduler.create_schedule_group(name=group_name, tags=tags)


def delete_schedule_group(campaign: Campaign) -> None:
    "function"
    group_name = f"campaign_{campaign.id}_group"

    # Delete the schedule group
    scheduler.delete_schedule_group(name=group_name)


def _build_schedule_params(campaign: Campaign) -> dict:
    """Build common parameters for creating or updating a campaign schedule."""
    schedule_expression = campaign.campaign_schedule

    # For one-time schedules, flexible time window is OFF
    flexible_time_window = {"Mode": "OFF"}

    # Create the target configuration
    target = {
        "Arn": TARGET_ARN,
        "Input": json.dumps(
            {
                "campaign_id": campaign.id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        "RoleArn": EXECUTION_ROLE_ARN,
    }
    schedule_name = f"campaign_{campaign.id}_schedule"
    group_name = f"campaign_{campaign.id}_group"
    description = f"Schedule for campaign {campaign.name} (ID: {campaign.id})"

    return {
        "name": schedule_name,
        "schedule_expression": schedule_expression,
        "flexible_time_window": flexible_time_window,
        "target": target,
        "group_name": group_name,
        "description": description,
        "state": "ENABLED",
    }


def create_campaign_schedule(campaign: Campaign) -> None:
    "function"
    params = _build_schedule_params(campaign)

    # Create the schedule
    scheduler.create_schedule(**params)


def update_campaign_schedule(campaign: Campaign) -> None:
    "function"
    params = _build_schedule_params(campaign)

    # Update the schedule
    scheduler.update_schedule(**params)


def get_campaign_schedule(campaign: Campaign) -> dict | None:
    "function"
    schedule_name = f"campaign_{campaign.id}_schedule"
    group_name = f"campaign_{campaign.id}_group"

    # Retrieve the schedule
    return scheduler.get_schedule(name=schedule_name, group_name=group_name)
