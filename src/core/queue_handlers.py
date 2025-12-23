"""
Queue message handlers for SQS message processing.
"""

import json
import logging

from aws_v2.models.sqs import SQSMessage

from core.scheduler import create_cycle_schedules
from services import campaign_service

logger = logging.getLogger(__name__)


async def queue_1_handler(message: SQSMessage) -> None:
    """Handle messages from Queue 1 to create cycle schedules for a campaign."""
    logger.info("Processing message from Queue 1: %s", message.body)
    campaign_id = json.loads(message.body).get("campaign_id")
    if campaign_id:
        campaign = await campaign_service.get_campaign(campaign_id)
        if campaign:
            logger.debug("Retrieved campaign: %s", campaign)
            await create_cycle_schedules(campaign)
        else:
            logger.warning("Campaign with ID %s not found", campaign_id)


async def queue_2_handler(message: SQSMessage) -> None:
    """Handle messages from Queue 2 to execute campaign cycle logic."""
    # {"campaign_id": 1, "cycle_count": 1, "timestamp": "2025-11-19T01:10:49.438461+00:00"}
    logger.info("Processing message from Queue 2: %s", message.body)
    data = json.loads(message.body)
    campaign_id = data.get("campaign_id")
    cycle_count = data.get("cycle_count")
    logger.info("Campaign ID: %s, Cycle Count: %s", campaign_id, cycle_count)

    campaign = await campaign_service.get_campaign(campaign_id)
    if campaign:
        logger.debug("Retrieved campaign: %s", campaign)
    # this is where we would trigger the campaign cycle execution logic
