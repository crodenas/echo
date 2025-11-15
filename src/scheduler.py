"""
Scheduler utilities for creating one-time schedules.
"""

import asyncio
import json
from datetime import datetime, timezone

from aws_croniter import AwsCroniter

import config
from aws import scheduler
from aws.models.scheduler import Schedule
from models import Campaign

QUEUE_1_ARN: str = config.QUEUE_1_ARN
QUEUE_2_ARN: str = config.QUEUE_2_ARN
EXECUTION_ROLE_ARN: str = config.EXECUTION_ROLE_ARN


async def create_schedule_group(campaign: Campaign) -> None:
    "function"
    group_name = f"campaign_{campaign.id}_group"
    tags = [{"Key": "CampaignID", "Value": str(campaign.id)}]

    # Create the schedule group
    await asyncio.to_thread(scheduler.create_schedule_group, name=group_name, tags=tags)


async def delete_schedule_group(campaign: Campaign) -> None:
    "function"
    group_name = f"campaign_{campaign.id}_group"

    # Delete the schedule group
    await asyncio.to_thread(scheduler.delete_schedule_group, name=group_name)


async def list_schedules(campaign: Campaign) -> list[Schedule]:
    "function"
    group_name = f"campaign_{campaign.id}_group"

    # List schedules in the group
    response = await asyncio.to_thread(scheduler.list_schedules, group_name=group_name)
    schedules = []
    for summary in response.schedules:
        full_schedule = await asyncio.to_thread(
            scheduler.get_schedule, name=summary.name, group_name=group_name
        )
        schedules.append(full_schedule)
    return schedules


def _build_campaign_schedule_params(campaign: Campaign) -> dict:
    """Build common parameters for creating or updating a campaign schedule."""
    schedule_expression = campaign.campaign_schedule

    # For one-time schedules, flexible time window is OFF
    flexible_time_window = {"Mode": "OFF"}

    # Create the target configuration
    target = {
        "Arn": QUEUE_1_ARN,
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


def _build_cycle_schedule_params(
    campaign: Campaign, schedule_expression: str, count: int
) -> dict:
    """Build common parameters for creating or updating a campaign cycle schedule."""

    # For one-time schedules, flexible time window is OFF
    flexible_time_window = {"Mode": "OFF"}

    # Create the target configuration
    target = {
        "Arn": QUEUE_2_ARN,
        "Input": json.dumps(
            {
                "campaign_id": campaign.id,
                "cycle_count": count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        "RoleArn": EXECUTION_ROLE_ARN,
    }
    schedule_name = f"campaign_{campaign.id}_schedule"
    group_name = f"campaign_{campaign.id}_group"
    description = (
        f"Schedule for campaign {campaign.name} (ID: {campaign.id}, cycle {count})"
    )

    return {
        "name": schedule_name,
        "schedule_expression": schedule_expression,
        "flexible_time_window": flexible_time_window,
        "target": target,
        "group_name": group_name,
        "description": description,
        "state": "ENABLED",
    }


async def create_campaign_schedule(campaign: Campaign) -> None:
    "function"
    params = _build_campaign_schedule_params(campaign)

    # Create the schedule
    await asyncio.to_thread(scheduler.create_schedule, **params)


async def update_campaign_schedule(campaign: Campaign) -> None:
    "function"
    params = _build_campaign_schedule_params(campaign)

    # Update the schedule
    await asyncio.to_thread(scheduler.update_schedule, **params)


async def get_campaign_schedule(campaign: Campaign) -> Schedule | None:
    "function"
    schedule_name = f"campaign_{campaign.id}_schedule"
    group_name = f"campaign_{campaign.id}_group"

    # Retrieve the schedule
    return await asyncio.to_thread(
        scheduler.get_schedule, name=schedule_name, group_name=group_name
    )


async def create_cycle_schedules(campaign: Campaign) -> dict:
    "function"
    # We want to use the cycle schedule expression to create campaign.max_events one-time
    # schedules that will trigger the campaign cycle execution.
    cron_iter = AwsCroniter(campaign.cycle_schedule)
    next_dates = cron_iter.get_next(datetime.now(timezone.utc), campaign.max_events)
    for count, next_execution in enumerate(next_dates):
        schedule_expression = next_execution.strftime("at(%Y-%m-%dT%H:%M:%S)")
        print(
            f"Creating cycle schedule {count + 1}/{campaign.max_events} for campaign "
            f"{campaign.id} at {schedule_expression}"
        )
        params = _build_cycle_schedule_params(campaign, schedule_expression, count + 1)
        # Create the cycle event schedule
        await asyncio.to_thread(scheduler.create_schedule, **params)

    return {
        "cycle_schedule": campaign.cycle_schedule,
        "max_events": campaign.max_events,
        "next_execution_dates": next_dates,
    }
