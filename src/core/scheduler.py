"""
Scheduler utilities for creating one-time schedules.
"""

import asyncio
import json
from datetime import datetime, timezone

from aws_croniter import AwsCroniter
from aws_v2 import scheduler
from aws_v2.models.scheduler import Schedule
from aws_v2.sqs import SQSMessage

from core import campaign as campaign_module
from core import config
from core.models import Campaign

QUEUE_1_URL: str = config.QUEUE_1_URL
QUEUE_1_ARN: str = config.QUEUE_1_ARN
QUEUE_2_URL: str = config.QUEUE_2_URL
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
    schedule_name = f"campaign_{campaign.id}_cycle_{count}_schedule"
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
        "action_after_completion": "DELETE",
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


def strip_cron_wrapper(cron_expression: str) -> str:
    "function"
    expr = cron_expression.strip()
    if expr.startswith("cron(") and expr.endswith(")"):
        return expr[5:-1]
    return expr


async def create_cycle_schedules(campaign: Campaign) -> None:
    "function"
    # We want to use the cycle schedule expression to create campaign.max_events one-time
    # schedules that will trigger the campaign cycle execution.
    # Strip 'cron()' wrapper if present
    cycle_expr = strip_cron_wrapper(campaign.cycle_schedule)
    cron_iter = AwsCroniter(cycle_expr)
    next_dates = cron_iter.get_next(
        from_date=datetime.now(timezone.utc), n=campaign.max_events
    )
    for count, next_execution in enumerate(next_dates):
        # it's only possible to have None here if the cron expression is invalid (or n=0?), so shouldn't happen
        if next_execution is not None:
            schedule_expression = next_execution.strftime("at(%Y-%m-%dT%H:%M:%S)")
        else:
            print(
                f"Skipping schedule creation for campaign {campaign.id} due to None next_execution."
            )
            continue
        print(
            f"Creating cycle schedule {count + 1}/{campaign.max_events} for campaign "
            f"{campaign.id} at {schedule_expression}"
        )
        params = _build_cycle_schedule_params(campaign, schedule_expression, count + 1)
        # Create the cycle event schedule
        await asyncio.to_thread(scheduler.create_schedule, **params)


async def queue_1_handler(message: SQSMessage) -> None:
    "function"
    print(f"Processing message from Queue 1: {message.body}")
    campaign_id = json.loads(message.body).get("campaign_id")
    if campaign_id:
        # Local import to avoid circular dependency with campaign module
        from . import campaign as campaign_module

        campaign = await campaign_module.get_campaign(campaign_id)
        if campaign:
            print(f"Retrieved campaign: {campaign}")
            await create_cycle_schedules(campaign)
        else:
            print(f"Campaign with ID {campaign_id} not found.")


async def queue_2_handler(message: SQSMessage) -> None:
    "function"
    # {"campaign_id": 1, "cycle_count": 1, "timestamp": "2025-11-19T01:10:49.438461+00:00"}
    print(f"Processing message from Queue 2: {message.body}")
    campaign_id = json.loads(message.body).get("campaign_id")
    cycle_count = json.loads(message.body).get("cycle_count")
    print(f"Campaign ID: {campaign_id}, Cycle Count: {cycle_count}")

    campaign = await campaign_module.get_campaign(campaign_id)
    if campaign:
        print(f"Retrieved campaign: {campaign}")
    # this is where we would trigger the campaign cycle execution logic
