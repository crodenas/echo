"""Retry logic for AWS operations with exponential backoff.

This module provides retry decorators and utilities for handling transient
AWS failures, throttling, and network errors.
"""

import logging
from typing import Any

from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    after_log,
)

from core.exceptions import (
    AWSCredentialsError,
    AWSThrottlingError,
    ScheduleNotFoundError,
    ScheduleGroupNotFoundError,
    ValidationError,
    is_retryable_error,
)
from core.settings import get_settings

# Get logger for this module
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()


def should_retry_aws_operation(exception: BaseException) -> bool:
    """Determine if an AWS operation should be retried.

    Args:
        exception: The exception that occurred

    Returns:
        bool: True if the operation should be retried
    """
    # Never retry validation errors or credential errors
    if isinstance(exception, (ValidationError, AWSCredentialsError)):
        return False

    # Never retry not-found errors (they won't resolve with retries)
    if isinstance(exception, (ScheduleNotFoundError, ScheduleGroupNotFoundError)):
        return False

    # Use our utility function for other cases
    return is_retryable_error(exception)


def aws_retry_decorator(
    *,
    max_attempts: int | None = None,
    min_wait: int | None = None,
    max_wait: int | None = None,
    operation_name: str = "AWS operation",
):
    """Create a retry decorator for AWS operations.

    Uses exponential backoff with jitter for retrying transient failures.

    Args:
        max_attempts: Maximum number of retry attempts (from settings if None)
        min_wait: Minimum wait time in seconds (from settings if None)
        max_wait: Maximum wait time in seconds (from settings if None)
        operation_name: Name of operation for logging purposes

    Returns:
        Retry decorator configured for AWS operations

    Example:
        @aws_retry_decorator(operation_name="create_schedule")
        async def create_schedule(...):
            ...
    """
    # Use settings defaults if not specified
    max_attempts = max_attempts or settings.aws.max_retry_attempts
    min_wait = min_wait or settings.aws.retry_min_wait
    max_wait = max_wait or settings.aws.retry_max_wait

    return retry(
        # Retry condition
        retry=retry_if_exception(should_retry_aws_operation),
        # Stop after N attempts
        stop=stop_after_attempt(max_attempts),
        # Exponential backoff with jitter
        wait=wait_exponential(
            multiplier=1,
            min=min_wait,
            max=max_wait,
        ),
        # Logging
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.DEBUG),
        # Reraise the last exception if all retries fail
        reraise=True,
    )


# Decorator for scheduler operations (higher timeout tolerance)
scheduler_retry = aws_retry_decorator(
    operation_name="EventBridge Scheduler operation",
)

# Decorator for SQS operations (lower timeout tolerance)
sqs_retry = aws_retry_decorator(
    max_attempts=2,  # Fewer retries for SQS
    max_wait=5,  # Shorter max wait for SQS
    operation_name="SQS operation",
)


def log_retry_attempt(
    retry_state: Any,
    operation_name: str,
    context: dict[str, Any] | None = None,
) -> None:
    """Log detailed information about a retry attempt.

    Args:
        retry_state: The tenacity retry state
        operation_name: Name of the operation being retried
        context: Additional context to include in logs
    """
    attempt_number = retry_state.attempt_number
    outcome = retry_state.outcome

    log_context = {
        "operation": operation_name,
        "attempt": attempt_number,
        **(context or {}),
    }

    if outcome.failed:
        exception = outcome.exception()
        log_context["error_type"] = type(exception).__name__
        log_context["error_message"] = str(exception)

        logger.warning(
            f"Retry attempt {attempt_number} for {operation_name} failed",
            extra=log_context,
        )
    else:
        logger.info(
            f"Operation {operation_name} succeeded after {attempt_number} attempts",
            extra=log_context,
        )


class RetryContext:
    """Context manager for tracking retry statistics.

    Usage:
        with RetryContext("create_schedule", campaign_id=123) as ctx:
            result = await some_aws_operation()
            ctx.success = True
    """

    def __init__(self, operation_name: str, **context):
        """Initialize retry context.

        Args:
            operation_name: Name of the operation
            **context: Additional context (campaign_id, etc.)
        """
        self.operation_name = operation_name
        self.context = context
        self.success = False
        self.error: Exception | None = None

    def __enter__(self):
        """Enter the context."""
        logger.debug(
            f"Starting {self.operation_name}",
            extra={"operation": self.operation_name, **self.context},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and log results."""
        if exc_val:
            self.error = exc_val
            logger.error(
                f"{self.operation_name} failed",
                extra={
                    "operation": self.operation_name,
                    "error_type": type(exc_val).__name__,
                    "error_message": str(exc_val),
                    **self.context,
                },
            )
        elif self.success:
            logger.info(
                f"{self.operation_name} completed successfully",
                extra={"operation": self.operation_name, **self.context},
            )
        return False  # Don't suppress exceptions
