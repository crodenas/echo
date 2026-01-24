"""Scheduler utilities for creating one-time schedules.

This module provides AWS EventBridge Scheduler operations with comprehensive
error handling, retry logic, and timeout protection.
"""

import asyncio
import json
from datetime import datetime, timezone

from aws_croniter import AwsCroniter
from aws_v2 import scheduler
from aws_v2.models.scheduler import Schedule

from core.aws_retry import scheduler_retry
from core.exceptions import (
    ScheduleAlreadyExistsError,
    ScheduleConflictError,
    ScheduleGroupAlreadyExistsError,
    ScheduleGroupNotFoundError,
    ScheduleNotFoundError,
    SchedulerError,
    extract_aws_error_code,
)
from core.logger import get_logger
from core.models import Campaign
from core.settings import get_settings

logger = get_logger(__name__)

# Load settings
settings = get_settings()

# AWS configuration from settings
QUEUE_1_ARN: str = settings.aws.queue_1_arn
QUEUE_2_ARN: str = settings.aws.queue_2_arn
EXECUTION_ROLE_ARN: str = settings.aws.execution_role_arn
SCHEDULER_TIMEOUT: int = settings.aws.scheduler_operation_timeout


def _handle_scheduler_error(error: Exception, operation: str, context: dict) -> None:
    """Convert AWS scheduler errors to application exceptions.

    Args:
        error: The original AWS exception
        operation: Name of the operation (for logging)
        context: Additional context (campaign_id, etc.)

    Raises:
        SchedulerError: Appropriate scheduler exception based on error type
    """
    error_code = extract_aws_error_code(error)

    logger.error(
        f"Scheduler operation '{operation}' failed",
        extra={
            "operation": operation,
            "error_code": error_code,
            "error_message": str(error),
            **context,
        },
    )

    # Map AWS error codes to application exceptions
    if error_code == "ResourceNotFoundException":
        # Determine if it's a schedule or schedule group
        if "schedule group" in str(error).lower():
            raise ScheduleGroupNotFoundError(
                f"Schedule group not found for {operation}",
                context=context,
                original_error=error,
                aws_error_code=error_code,
            ) from error
        else:
            raise ScheduleNotFoundError(
                f"Schedule not found for {operation}",
                context=context,
                original_error=error,
                aws_error_code=error_code,
            ) from error

    elif error_code == "ConflictException":
        # Check if it's a "already exists" conflict
        error_msg = str(error).lower()
        if "already exists" in error_msg:
            if "schedule group" in error_msg:
                raise ScheduleGroupAlreadyExistsError(
                    f"Schedule group already exists for {operation}",
                    context=context,
                    original_error=error,
                    aws_error_code=error_code,
                ) from error
            else:
                raise ScheduleAlreadyExistsError(
                    f"Schedule already exists for {operation}",
                    context=context,
                    original_error=error,
                    aws_error_code=error_code,
                ) from error
        else:
            raise ScheduleConflictError(
                f"Schedule operation conflict for {operation}",
                context=context,
                original_error=error,
                aws_error_code=error_code,
            ) from error

    # Generic scheduler error for all other cases
    raise SchedulerError(
        f"Scheduler operation failed: {operation}",
        context=context,
        original_error=error,
        aws_error_code=error_code,
    ) from error


@scheduler_retry
async def create_schedule_group(campaign: Campaign) -> None:
    """Create an AWS EventBridge schedule group for a campaign.

    Args:
        campaign: The campaign to create a schedule group for

    Raises:
        ScheduleGroupAlreadyExistsError: If group already exists (safe to ignore)
        SchedulerError: For other AWS scheduler errors
    """
    group_name = f"campaign_{campaign.id}_group"
    tags = [{"Key": "CampaignID", "Value": str(campaign.id)}]
    context = {"campaign_id": campaign.id, "group_name": group_name}

    logger.info(
        f"Creating schedule group for campaign {campaign.id}",
        extra=context,
    )

    try:
        await asyncio.wait_for(
            asyncio.to_thread(scheduler.create_schedule_group, name=group_name, tags=tags),
            timeout=SCHEDULER_TIMEOUT,
        )
        logger.info(
            f"Successfully created schedule group for campaign {campaign.id}",
            extra=context,
        )
    except asyncio.TimeoutError as e:
        logger.error(
            f"Timeout creating schedule group for campaign {campaign.id}",
            extra=context,
        )
        raise SchedulerError(
            f"Timeout creating schedule group (>{SCHEDULER_TIMEOUT}s)",
            context=context,
            original_error=e,
        ) from e
    except ScheduleGroupAlreadyExistsError:
        # This is idempotent - group already exists is OK
        logger.info(
            f"Schedule group already exists for campaign {campaign.id}",
            extra=context,
        )
        raise  # Re-raise so caller can handle if needed
    except Exception as e:
        _handle_scheduler_error(e, "create_schedule_group", context)


@scheduler_retry
async def delete_schedule_group(campaign: Campaign) -> None:
    """Delete an AWS EventBridge schedule group for a campaign.

    Args:
        campaign: The campaign whose schedule group to delete

    Raises:
        ScheduleGroupNotFoundError: If group doesn't exist (safe to ignore)
        SchedulerError: For other AWS scheduler errors
    """
    group_name = f"campaign_{campaign.id}_group"
    context = {"campaign_id": campaign.id, "group_name": group_name}

    logger.info(
        f"Deleting schedule group for campaign {campaign.id}",
        extra=context,
    )

    try:
        await asyncio.wait_for(
            asyncio.to_thread(scheduler.delete_schedule_group, name=group_name),
            timeout=SCHEDULER_TIMEOUT,
        )
        logger.info(
            f"Successfully deleted schedule group for campaign {campaign.id}",
            extra=context,
        )
    except asyncio.TimeoutError as e:
        logger.error(
            f"Timeout deleting schedule group for campaign {campaign.id}",
            extra=context,
        )
        raise SchedulerError(
            f"Timeout deleting schedule group (>{SCHEDULER_TIMEOUT}s)",
            context=context,
            original_error=e,
        ) from e
    except ScheduleGroupNotFoundError:
        # Group doesn't exist - that's fine for deletion
        logger.info(
            f"Schedule group not found for campaign {campaign.id} (already deleted)",
            extra=context,
        )
        raise  # Re-raise so caller can decide how to handle
    except Exception as e:
        _handle_scheduler_error(e, "delete_schedule_group", context)


@scheduler_retry
async def list_schedules(campaign: Campaign) -> list[Schedule]:
    """List all schedules in a campaign's schedule group.

    Args:
        campaign: The campaign whose schedules to list

    Returns:
        list[Schedule]: List of schedules in the group

    Raises:
        ScheduleGroupNotFoundError: If schedule group doesn't exist
        SchedulerError: For other AWS scheduler errors
    """
    group_name = f"campaign_{campaign.id}_group"
    context = {"campaign_id": campaign.id, "group_name": group_name}

    logger.debug(
        f"Listing schedules for campaign {campaign.id}",
        extra=context,
    )

    try:
        # List schedules with timeout
        response = await asyncio.wait_for(
            asyncio.to_thread(scheduler.list_schedules, group_name=group_name),
            timeout=SCHEDULER_TIMEOUT,
        )

        # Fetch full details for each schedule
        schedules = []
        for summary in response.schedules:
            try:
                full_schedule = await asyncio.wait_for(
                    asyncio.to_thread(
                        scheduler.get_schedule,
                        name=summary.name,
                        group_name=group_name,
                    ),
                    timeout=SCHEDULER_TIMEOUT,
                )
                schedules.append(full_schedule)
            except Exception as e:
                # Log but continue with other schedules
                logger.warning(
                    f"Failed to get details for schedule {summary.name}",
                    extra={
                        **context,
                        "schedule_name": summary.name,
                        "error": str(e),
                    },
                )

        logger.debug(
            f"Found {len(schedules)} schedules for campaign {campaign.id}",
            extra={**context, "schedule_count": len(schedules)},
        )
        return schedules

    except asyncio.TimeoutError as e:
        logger.error(
            f"Timeout listing schedules for campaign {campaign.id}",
            extra=context,
        )
        raise SchedulerError(
            f"Timeout listing schedules (>{SCHEDULER_TIMEOUT}s)",
            context=context,
            original_error=e,
        ) from e
    except Exception as e:
        _handle_scheduler_error(e, "list_schedules", context)


def _build_campaign_schedule_params(campaign: Campaign) -> dict:
    """Build common parameters for creating or updating a campaign schedule."""
    schedule_expression = campaign.campaign_schedule

    # For recurring schedules, flexible time window is OFF
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


@scheduler_retry
async def create_campaign_schedule(campaign: Campaign) -> None:
    """Create the main schedule for a campaign.

    Args:
        campaign: The campaign to create a schedule for

    Raises:
        ScheduleAlreadyExistsError: If schedule already exists
        ScheduleGroupNotFoundError: If schedule group doesn't exist
        SchedulerError: For other AWS scheduler errors
    """
    params = _build_campaign_schedule_params(campaign)
    context = {
        "campaign_id": campaign.id,
        "schedule_name": params["name"],
        "schedule_expression": params["schedule_expression"],
    }

    logger.info(
        f"Creating campaign schedule for campaign {campaign.id}",
        extra=context,
    )

    try:
        await asyncio.wait_for(
            asyncio.to_thread(scheduler.create_schedule, **params),
            timeout=SCHEDULER_TIMEOUT,
        )
        logger.info(
            f"Successfully created campaign schedule for campaign {campaign.id}",
            extra=context,
        )
    except asyncio.TimeoutError as e:
        logger.error(
            f"Timeout creating campaign schedule for campaign {campaign.id}",
            extra=context,
        )
        raise SchedulerError(
            f"Timeout creating campaign schedule (>{SCHEDULER_TIMEOUT}s)",
            context=context,
            original_error=e,
        ) from e
    except Exception as e:
        _handle_scheduler_error(e, "create_campaign_schedule", context)


@scheduler_retry
async def update_campaign_schedule(campaign: Campaign) -> None:
    """Update an existing campaign schedule.

    Args:
        campaign: The campaign whose schedule to update

    Raises:
        ScheduleNotFoundError: If schedule doesn't exist
        ScheduleGroupNotFoundError: If schedule group doesn't exist
        SchedulerError: For other AWS scheduler errors
    """
    params = _build_campaign_schedule_params(campaign)
    context = {
        "campaign_id": campaign.id,
        "schedule_name": params["name"],
        "schedule_expression": params["schedule_expression"],
    }

    logger.info(
        f"Updating campaign schedule for campaign {campaign.id}",
        extra=context,
    )

    try:
        await asyncio.wait_for(
            asyncio.to_thread(scheduler.update_schedule, **params),
            timeout=SCHEDULER_TIMEOUT,
        )
        logger.info(
            f"Successfully updated campaign schedule for campaign {campaign.id}",
            extra=context,
        )
    except asyncio.TimeoutError as e:
        logger.error(
            f"Timeout updating campaign schedule for campaign {campaign.id}",
            extra=context,
        )
        raise SchedulerError(
            f"Timeout updating campaign schedule (>{SCHEDULER_TIMEOUT}s)",
            context=context,
            original_error=e,
        ) from e
    except Exception as e:
        _handle_scheduler_error(e, "update_campaign_schedule", context)


@scheduler_retry
async def get_campaign_schedule(campaign: Campaign) -> Schedule | None:
    """Retrieve the schedule for a campaign.

    Args:
        campaign: The campaign whose schedule to retrieve

    Returns:
        Schedule | None: The schedule, or None if not found

    Raises:
        SchedulerError: For AWS scheduler errors (except not found)
    """
    schedule_name = f"campaign_{campaign.id}_schedule"
    group_name = f"campaign_{campaign.id}_group"
    context = {
        "campaign_id": campaign.id,
        "schedule_name": schedule_name,
        "group_name": group_name,
    }

    logger.debug(
        f"Getting campaign schedule for campaign {campaign.id}",
        extra=context,
    )

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                scheduler.get_schedule,
                name=schedule_name,
                group_name=group_name,
            ),
            timeout=SCHEDULER_TIMEOUT,
        )
        logger.debug(
            f"Successfully retrieved campaign schedule for campaign {campaign.id}",
            extra=context,
        )
        return result
    except asyncio.TimeoutError as e:
        logger.error(
            f"Timeout getting campaign schedule for campaign {campaign.id}",
            extra=context,
        )
        raise SchedulerError(
            f"Timeout getting campaign schedule (>{SCHEDULER_TIMEOUT}s)",
            context=context,
            original_error=e,
        ) from e
    except ScheduleNotFoundError:
        # Return None for not found (common case)
        logger.debug(
            f"Campaign schedule not found for campaign {campaign.id}",
            extra=context,
        )
        return None
    except Exception as e:
        _handle_scheduler_error(e, "get_campaign_schedule", context)


def strip_cron_wrapper(cron_expression: str) -> str:
    """Strip the 'cron()' wrapper from an AWS cron expression if present."""
    expr = cron_expression.strip()
    if expr.startswith("cron(") and expr.endswith(")"):
        return expr[5:-1]
    return expr


async def create_cycle_schedules(campaign: Campaign) -> dict[str, int]:
    """Create one-time schedules for each cycle event in a campaign.

    This is a critical operation that creates multiple schedules. Errors are
    logged but don't stop the entire operation - we track success/failure counts.

    Args:
        campaign: The campaign to create cycle schedules for

    Returns:
        dict with 'success' and 'failed' counts

    Raises:
        SchedulerError: For critical errors (invalid cron, group not found)
    """
    context = {"campaign_id": campaign.id, "max_events": campaign.max_events}

    logger.info(
        f"Creating {campaign.max_events} cycle schedules for campaign {campaign.id}",
        extra=context,
    )

    # Strip 'cron()' wrapper if present
    cycle_expr = strip_cron_wrapper(campaign.cycle_schedule)

    try:
        cron_iter = AwsCroniter(cycle_expr)
        next_dates = cron_iter.get_next(
            from_date=datetime.now(timezone.utc), n=campaign.max_events
        )
    except Exception as e:
        logger.error(
            f"Invalid cron expression for campaign {campaign.id}",
            extra={**context, "cycle_schedule": campaign.cycle_schedule, "error": str(e)},
        )
        raise SchedulerError(
            f"Invalid cycle schedule cron expression: {campaign.cycle_schedule}",
            context=context,
            original_error=e,
        ) from e

    # Track success/failure counts
    success_count = 0
    failed_count = 0

    for count, next_execution in enumerate(next_dates, start=1):
        if next_execution is None:
            logger.warning(
                f"Skipping schedule {count} for campaign {campaign.id} - no next execution",
                extra={**context, "cycle_count": count},
            )
            failed_count += 1
            continue

        schedule_expression = next_execution.strftime("at(%Y-%m-%dT%H:%M:%S)")
        schedule_context = {
            **context,
            "cycle_count": count,
            "schedule_expression": schedule_expression,
        }

        logger.info(
            f"Creating cycle schedule {count}/{campaign.max_events} for campaign {campaign.id}",
            extra=schedule_context,
        )

        params = _build_cycle_schedule_params(campaign, schedule_expression, count)

        try:
            # Use retry decorator via direct call
            await asyncio.wait_for(
                asyncio.to_thread(scheduler.create_schedule, **params),
                timeout=SCHEDULER_TIMEOUT,
            )
            success_count += 1
            logger.info(
                f"Successfully created cycle schedule {count} for campaign {campaign.id}",
                extra=schedule_context,
            )
        except asyncio.TimeoutError as e:
            failed_count += 1
            logger.error(
                f"Timeout creating cycle schedule {count} for campaign {campaign.id}",
                extra=schedule_context,
            )
            # Continue with other schedules
        except ScheduleAlreadyExistsError:
            # Already exists is OK - count as success
            success_count += 1
            logger.info(
                f"Cycle schedule {count} already exists for campaign {campaign.id}",
                extra=schedule_context,
            )
        except Exception as e:
            failed_count += 1
            logger.error(
                f"Failed to create cycle schedule {count} for campaign {campaign.id}",
                extra={**schedule_context, "error": str(e)},
            )
            # Continue with other schedules

    result = {"success": success_count, "failed": failed_count}
    logger.info(
        f"Completed cycle schedule creation for campaign {campaign.id}",
        extra={**context, **result},
    )

    return result
