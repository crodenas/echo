"""Application lifecycle management.

This module handles FastAPI application startup and shutdown events,
including SQS consumer management and AWS connectivity validation.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.exceptions import AWSCredentialsError, ConfigurationError
from core.logger import get_logger
from core.queue_handlers import queue_1_handler, queue_2_handler
from core.settings import get_settings
from utils.queue_watcher import create_sqs_consumer

logger = get_logger(__name__)

# Load settings
settings = get_settings()

# ---------------------------------------------------------------------------
# Asynchronous SQS Consumers
# ---------------------------------------------------------------------------
_consumers = []  # SQSConsumer instances
_consumer_tasks: list[asyncio.Task] = []  # Associated asyncio tasks


async def validate_aws_connectivity() -> None:
    """Validate AWS credentials and basic connectivity on startup.

    Performs lightweight validation to ensure the application can connect
    to AWS services before starting the queue consumers.

    Raises:
        AWSCredentialsError: If AWS credentials are invalid or missing
        ConfigurationError: If AWS configuration is invalid
    """
    logger.info("Validating AWS connectivity and configuration")

    try:
        # Import here to avoid circular dependencies
        from aws_v2 import scheduler, sqs

        # Test 1: Validate scheduler access (lightweight list operation)
        logger.debug("Testing EventBridge Scheduler access")
        try:
            # List schedule groups (limited to 1 for quick validation)
            await asyncio.to_thread(
                scheduler.list_schedule_groups,
                max_results=1,
            )
            logger.info("EventBridge Scheduler access validated")
        except Exception as e:
            error_msg = str(e).lower()
            if any(cred_err in error_msg for cred_err in ["credentials", "access denied", "unauthorized"]):
                logger.critical(
                    "AWS credentials error - invalid or missing credentials",
                    extra={"error": str(e)},
                )
                raise AWSCredentialsError(
                    "AWS credentials are invalid or missing for EventBridge Scheduler",
                    original_error=e,
                ) from e
            else:
                logger.error(
                    "Failed to access EventBridge Scheduler",
                    extra={"error": str(e)},
                )
                raise ConfigurationError(
                    "Failed to access EventBridge Scheduler",
                    original_error=e,
                ) from e

        # Test 2: Validate SQS queue access
        logger.debug("Testing SQS queue access")
        try:
            # Validate Queue 1 access (receive with 0 wait time for quick check)
            await asyncio.to_thread(
                sqs.receive_message,
                queue_url=settings.aws.queue_1_url,
                max_messages=1,
                wait_time_seconds=0,
            )
            logger.info(
                "SQS Queue 1 access validated",
                extra={"queue_url": settings.aws.queue_1_url},
            )

            # Validate Queue 2 access
            await asyncio.to_thread(
                sqs.receive_message,
                queue_url=settings.aws.queue_2_url,
                max_messages=1,
                wait_time_seconds=0,
            )
            logger.info(
                "SQS Queue 2 access validated",
                extra={"queue_url": settings.aws.queue_2_url},
            )
        except Exception as e:
            error_msg = str(e).lower()
            if any(cred_err in error_msg for cred_err in ["credentials", "access denied", "unauthorized"]):
                logger.critical(
                    "AWS credentials error - invalid or missing credentials",
                    extra={"error": str(e)},
                )
                raise AWSCredentialsError(
                    "AWS credentials are invalid or missing for SQS",
                    original_error=e,
                ) from e
            elif "nonexistentqueue" in error_msg or "does not exist" in error_msg:
                logger.critical(
                    "SQS queue not found - check queue URLs in configuration",
                    extra={
                        "queue_1_url": settings.aws.queue_1_url,
                        "queue_2_url": settings.aws.queue_2_url,
                        "error": str(e),
                    },
                )
                raise ConfigurationError(
                    "SQS queues not found - verify queue URLs in configuration",
                    original_error=e,
                ) from e
            else:
                logger.error(
                    "Failed to access SQS queues",
                    extra={"error": str(e)},
                )
                raise ConfigurationError(
                    "Failed to access SQS queues",
                    original_error=e,
                ) from e

        logger.info("AWS connectivity validation successful")

    except (AWSCredentialsError, ConfigurationError):
        # Re-raise known errors
        raise
    except Exception as e:
        logger.critical(
            "Unexpected error during AWS connectivity validation",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise ConfigurationError(
            "Unexpected error during AWS connectivity validation",
            original_error=e,
        ) from e


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifecycle event handler for the FastAPI application.

    This context manager handles startup and shutdown events:
    - On startup:
      1. Validates AWS connectivity and credentials
      2. Creates and starts SQS consumers as background asyncio tasks
    - On shutdown:
      1. Stops consumers gracefully
      2. Cancels running tasks
      3. Waits for cleanup to complete

    Args:
        _app: The FastAPI application instance (unused but required by FastAPI)

    Yields:
        None: Application runs while yielded
    """
    logger.info("Application startup initiated")

    try:
        # Step 1: Validate AWS connectivity (skip if configured)
        if settings.skip_aws_validation:
            logger.warning(
                "AWS validation skipped (SKIP_AWS_VALIDATION=true) - running in local development mode"
            )
        else:
            await validate_aws_connectivity()

        # Step 2: Create and start SQS consumers (skip if AWS validation is disabled)
        if not settings.skip_aws_validation:
            logger.info("Starting SQS consumers")

            consumer1 = create_sqs_consumer(
                queue_url=settings.aws.queue_1_url,
                max_messages=5,
            )
            consumer2 = create_sqs_consumer(
                queue_url=settings.aws.queue_2_url,
                max_messages=5,
            )

            _consumers.extend([consumer1, consumer2])

            # Start consumer tasks
            _consumer_tasks.append(
                asyncio.create_task(
                    consumer1.start_async(queue_1_handler),
                    name="queue_1_consumer",
                )
            )
            _consumer_tasks.append(
                asyncio.create_task(
                    consumer2.start_async(queue_2_handler),
                    name="queue_2_consumer",
                )
            )

            logger.info(
                "SQS consumers started successfully",
                extra={
                    "consumer_count": len(_consumers),
                    "queue_1_url": settings.aws.queue_1_url,
                    "queue_2_url": settings.aws.queue_2_url,
                },
            )

        logger.info("Application startup complete")

    except Exception as e:
        logger.critical(
            "Application startup failed",
            extra={"error": str(e)},
            exc_info=True,
        )
        # Clean up any partially started consumers
        for consumer in _consumers:
            consumer.stop()
        for task in _consumer_tasks:
            task.cancel()
        raise

    yield  # Application runs here

    # Shutdown: Stop consumers and cancel tasks
    logger.info("Application shutdown initiated")

    try:
        # Signal consumers to stop
        for consumer in _consumers:
            consumer.stop()

        # Cancel consumer tasks
        for task in _consumer_tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete (with timeout)
        if _consumer_tasks:
            await asyncio.wait_for(
                asyncio.gather(*_consumer_tasks, return_exceptions=True),
                timeout=10.0,
            )

        logger.info(
            "SQS consumers stopped successfully",
            extra={"consumer_count": len(_consumers)},
        )

    except asyncio.TimeoutError:
        logger.warning(
            "Consumer shutdown timed out after 10 seconds",
            extra={"consumer_count": len(_consumers)},
        )
    except Exception as e:
        logger.error(
            "Error during application shutdown",
            extra={"error": str(e)},
            exc_info=True,
        )
    finally:
        # Clear consumer lists
        _consumers.clear()
        _consumer_tasks.clear()
        logger.info("Application shutdown complete")
