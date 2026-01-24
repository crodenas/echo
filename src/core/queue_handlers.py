"""Queue message handlers for SQS message processing.

This module provides message handlers for SQS queues with comprehensive
error handling, validation, and structured logging.
"""

import json

from aws_v2.models.sqs import SQSMessage

from core.exceptions import (
    CampaignNotFoundError,
    MessageProcessingError,
    SchedulerError,
    ValidationError,
)
from core.logger import get_logger
from core.scheduler import create_cycle_schedules
from services import campaign_service

logger = get_logger(__name__)


def _validate_queue_1_message(data: dict) -> tuple[bool, str | None]:
    """Validate Queue 1 message structure.

    Args:
        data: Parsed message body

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Message body must be a JSON object"

    campaign_id = data.get("campaign_id")
    if campaign_id is None:
        return False, "Missing required field: campaign_id"

    if not isinstance(campaign_id, int):
        return False, f"campaign_id must be an integer, got {type(campaign_id).__name__}"

    return True, None


def _validate_queue_2_message(data: dict) -> tuple[bool, str | None]:
    """Validate Queue 2 message structure.

    Args:
        data: Parsed message body

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Message body must be a JSON object"

    campaign_id = data.get("campaign_id")
    if campaign_id is None:
        return False, "Missing required field: campaign_id"

    if not isinstance(campaign_id, int):
        return False, f"campaign_id must be an integer, got {type(campaign_id).__name__}"

    cycle_count = data.get("cycle_count")
    if cycle_count is None:
        return False, "Missing required field: cycle_count"

    if not isinstance(cycle_count, int):
        return False, f"cycle_count must be an integer, got {type(cycle_count).__name__}"

    return True, None


async def queue_1_handler(message: SQSMessage) -> None:
    """Handle messages from Queue 1 to create cycle schedules for a campaign.

    Queue 1 receives messages when a campaign is triggered to start. This handler
    creates all the cycle schedules for the campaign based on the cycle_schedule
    cron expression and max_events count.

    Expected message format:
        {
            "campaign_id": <int>,
            "timestamp": <ISO 8601 timestamp>
        }

    Args:
        message: The SQS message to process

    Raises:
        MessageProcessingError: For validation errors, JSON parsing errors
        CampaignNotFoundError: When campaign doesn't exist in database
        SchedulerError: When AWS scheduler operations fail
    """
    message_context = {
        "queue": "Queue1",
        "message_id": message.message_id,
    }

    logger.info(
        "Processing message from Queue 1",
        extra={**message_context, "body_preview": message.body[:100]},
    )

    # Step 1: Parse JSON
    try:
        data = json.loads(message.body)
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse Queue 1 message JSON",
            extra={
                **message_context,
                "error": str(e),
                "body": message.body,
            },
        )
        raise MessageProcessingError(
            "Invalid JSON in Queue 1 message",
            context=message_context,
            original_error=e,
        ) from e

    # Step 2: Validate message structure
    is_valid, error_msg = _validate_queue_1_message(data)
    if not is_valid:
        logger.error(
            "Queue 1 message validation failed",
            extra={
                **message_context,
                "error": error_msg,
                "data": data,
            },
        )
        raise ValidationError(
            f"Queue 1 message validation failed: {error_msg}",
            context={**message_context, "data": data},
        )

    campaign_id = data["campaign_id"]
    message_context["campaign_id"] = campaign_id

    logger.info(
        f"Creating cycle schedules for campaign {campaign_id}",
        extra=message_context,
    )

    # Step 3: Retrieve campaign
    try:
        campaign = await campaign_service.get_campaign(campaign_id)
    except Exception as e:
        logger.error(
            f"Failed to retrieve campaign {campaign_id}",
            extra={
                **message_context,
                "error_type": type(e).__name__,
                "error": str(e),
            },
        )
        raise

    if campaign is None:
        logger.warning(
            f"Campaign {campaign_id} not found in database",
            extra=message_context,
        )
        raise CampaignNotFoundError(
            f"Campaign {campaign_id} not found",
            context=message_context,
        )

    logger.debug(
        f"Retrieved campaign {campaign_id}",
        extra={
            **message_context,
            "campaign_name": campaign.name,
            "max_events": campaign.max_events,
        },
    )

    # Step 4: Create cycle schedules
    try:
        result = await create_cycle_schedules(campaign)
        logger.info(
            f"Cycle schedule creation completed for campaign {campaign_id}",
            extra={
                **message_context,
                "success_count": result["success"],
                "failed_count": result["failed"],
            },
        )

        # If some schedules failed, log warning but don't raise
        if result["failed"] > 0:
            logger.warning(
                f"{result['failed']} cycle schedules failed for campaign {campaign_id}",
                extra={
                    **message_context,
                    "success_count": result["success"],
                    "failed_count": result["failed"],
                },
            )
    except SchedulerError as e:
        logger.error(
            f"Scheduler error creating cycle schedules for campaign {campaign_id}",
            extra={
                **message_context,
                "error_type": type(e).__name__,
                "error": str(e),
            },
        )
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error creating cycle schedules for campaign {campaign_id}",
            extra={
                **message_context,
                "error_type": type(e).__name__,
                "error": str(e),
            },
        )
        raise MessageProcessingError(
            f"Failed to create cycle schedules for campaign {campaign_id}",
            context=message_context,
            original_error=e,
        ) from e


async def queue_2_handler(message: SQSMessage) -> None:
    """Handle messages from Queue 2 to execute campaign cycle logic.

    Queue 2 receives messages when a cycle schedule triggers. This handler
    executes the actual campaign cycle logic (TBD: send notifications, fetch data).

    Expected message format:
        {
            "campaign_id": <int>,
            "cycle_count": <int>,
            "timestamp": <ISO 8601 timestamp>
        }

    Args:
        message: The SQS message to process

    Raises:
        MessageProcessingError: For validation errors, JSON parsing errors
        CampaignNotFoundError: When campaign doesn't exist in database
    """
    message_context = {
        "queue": "Queue2",
        "message_id": message.message_id,
    }

    logger.info(
        "Processing message from Queue 2",
        extra={**message_context, "body_preview": message.body[:100]},
    )

    # Step 1: Parse JSON
    try:
        data = json.loads(message.body)
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse Queue 2 message JSON",
            extra={
                **message_context,
                "error": str(e),
                "body": message.body,
            },
        )
        raise MessageProcessingError(
            "Invalid JSON in Queue 2 message",
            context=message_context,
            original_error=e,
        ) from e

    # Step 2: Validate message structure
    is_valid, error_msg = _validate_queue_2_message(data)
    if not is_valid:
        logger.error(
            "Queue 2 message validation failed",
            extra={
                **message_context,
                "error": error_msg,
                "data": data,
            },
        )
        raise ValidationError(
            f"Queue 2 message validation failed: {error_msg}",
            context={**message_context, "data": data},
        )

    campaign_id = data["campaign_id"]
    cycle_count = data["cycle_count"]
    message_context["campaign_id"] = campaign_id
    message_context["cycle_count"] = cycle_count

    logger.info(
        f"Executing cycle {cycle_count} for campaign {campaign_id}",
        extra=message_context,
    )

    # Step 3: Retrieve campaign
    try:
        campaign = await campaign_service.get_campaign(campaign_id)
    except Exception as e:
        logger.error(
            f"Failed to retrieve campaign {campaign_id}",
            extra={
                **message_context,
                "error_type": type(e).__name__,
                "error": str(e),
            },
        )
        raise

    if campaign is None:
        logger.warning(
            f"Campaign {campaign_id} not found in database",
            extra=message_context,
        )
        raise CampaignNotFoundError(
            f"Campaign {campaign_id} not found",
            context=message_context,
        )

    logger.debug(
        f"Retrieved campaign {campaign_id} for cycle {cycle_count}",
        extra={
            **message_context,
            "campaign_name": campaign.name,
        },
    )

    # Step 4: Execute campaign cycle logic
    # TODO: Implement actual campaign cycle execution
    # This is where we would:
    # - Connect to the data source using campaign.conn_string
    # - Fetch data that needs verification
    # - Send notifications to resource owners
    # - Log results
    logger.info(
        f"Campaign cycle execution completed for campaign {campaign_id}, cycle {cycle_count}",
        extra=message_context,
    )
