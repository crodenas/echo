"""
Scheduler utilities for creating one-time schedules.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

from aws_croniter import AwsCroniter
from aws_v2 import scheduler
from aws_v2.models.scheduler import Schedule

from core import config
from core.models import Campaign

logger = logging.getLogger(__name__)

QUEUE_1_URL: str = config.QUEUE_1_URL
QUEUE_1_ARN: str = config.QUEUE_1_ARN
QUEUE_2_URL: str = config.QUEUE_2_URL
QUEUE_2_ARN: str = config.QUEUE_2_ARN
EXECUTION_ROLE_ARN: str = config.EXECUTION_ROLE_ARN


async def create_schedule_group(campaign: Campaign) -> None:
    """Create an AWS EventBridge schedule group for a campaign."""
    group_name = f"campaign_{campaign.id}_group"
    tags = [{"Key": "CampaignID", "Value": str(campaign.id)}]

    # Create the schedule group
    await asyncio.to_thread(scheduler.create_schedule_group, name=group_name, tags=tags)


async def delete_schedule_group(campaign: Campaign) -> None:
    """Delete an AWS EventBridge schedule group for a campaign."""
    group_name = f"campaign_{campaign.id}_group"

    # Delete the schedule group
    await asyncio.to_thread(scheduler.delete_schedule_group, name=group_name)


async def list_schedules(campaign: Campaign) -> list[Schedule]:
    """List all schedules in a campaign's schedule group."""
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
    """Create the main schedule for a campaign."""
    params = _build_campaign_schedule_params(campaign)

    # Create the schedule
    await asyncio.to_thread(scheduler.create_schedule, **params)


async def update_campaign_schedule(campaign: Campaign) -> None:
    """Update an existing campaign schedule."""
    params = _build_campaign_schedule_params(campaign)

    # Update the schedule
    await asyncio.to_thread(scheduler.update_schedule, **params)


async def get_campaign_schedule(campaign: Campaign) -> Schedule | None:
    """Retrieve the schedule for a campaign."""
    schedule_name = f"campaign_{campaign.id}_schedule"
    group_name = f"campaign_{campaign.id}_group"

    # Retrieve the schedule
    return await asyncio.to_thread(
        scheduler.get_schedule, name=schedule_name, group_name=group_name
    )


def strip_cron_wrapper(cron_expression: str) -> str:
    """Strip the 'cron()' wrapper from an AWS cron expression if present."""
    expr = cron_expression.strip()
    if expr.startswith("cron(") and expr.endswith(")"):
        return expr[5:-1]
    return expr


async def create_cycle_schedules(campaign: Campaign) -> None:
    """Create one-time schedules for each cycle event in a campaign."""
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
            logger.warning(
                "Skipping schedule creation for campaign %s due to None next_execution",
                campaign.id,
            )
            continue
        logger.info(
            "Creating cycle schedule %d/%d for campaign %s at %s",
            count + 1,
            campaign.max_events,
            campaign.id,
            schedule_expression,
        )
        params = _build_cycle_schedule_params(campaign, schedule_expression, count + 1)
        # Create the cycle event schedule
        await asyncio.to_thread(scheduler.create_schedule, **params)
