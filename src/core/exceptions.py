"""Exception hierarchy for ECHO application.

This module defines a comprehensive exception hierarchy for handling
AWS operations, database operations, and application-level errors.
"""

from typing import Any


class EchoError(Exception):
    """Base exception for all ECHO application errors.

    All custom exceptions in the application should inherit from this class.
    """

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize the exception.

        Args:
            message: Human-readable error message
            context: Additional context information (campaign_id, schedule_id, etc.)
            original_error: The original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.original_error = original_error

    def __str__(self) -> str:
        """Return string representation with context."""
        parts = [self.message]
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"(context: {context_str})")
        if self.original_error:
            parts.append(f"(caused by: {type(self.original_error).__name__})")
        return " ".join(parts)


# ============================================================================
# Configuration Errors
# ============================================================================


class ConfigurationError(EchoError):
    """Raised when application configuration is invalid or missing."""


# ============================================================================
# AWS Base Errors
# ============================================================================


class AWSOperationError(EchoError):
    """Base exception for all AWS operation errors.

    This is the parent class for all AWS-related errors (scheduler, SQS, etc.)
    """

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        original_error: Exception | None = None,
        aws_error_code: str | None = None,
    ):
        """Initialize the AWS operation error.

        Args:
            message: Human-readable error message
            context: Additional context (campaign_id, schedule_id, etc.)
            original_error: The original AWS SDK exception
            aws_error_code: AWS error code (e.g., 'ResourceNotFoundException')
        """
        super().__init__(message, context=context, original_error=original_error)
        self.aws_error_code = aws_error_code

    def __str__(self) -> str:
        """Return string representation with AWS error code."""
        base_str = super().__str__()
        if self.aws_error_code:
            return f"{base_str} (AWS error: {self.aws_error_code})"
        return base_str


class AWSCredentialsError(AWSOperationError):
    """Raised when AWS credentials are invalid, expired, or missing."""


class AWSThrottlingError(AWSOperationError):
    """Raised when AWS API calls are throttled.

    This is a retryable error - the operation should be retried with backoff.
    """


# ============================================================================
# EventBridge Scheduler Errors
# ============================================================================


class SchedulerError(AWSOperationError):
    """Base exception for EventBridge Scheduler operations."""


class ScheduleGroupNotFoundError(SchedulerError):
    """Raised when a schedule group does not exist.

    This typically indicates the campaign was deleted or never created.
    """


class ScheduleNotFoundError(SchedulerError):
    """Raised when a schedule does not exist.

    This can occur when trying to update or delete a non-existent schedule.
    """


class ScheduleGroupAlreadyExistsError(SchedulerError):
    """Raised when trying to create a schedule group that already exists.

    This is usually not an error - indicates idempotent operation.
    """


class ScheduleAlreadyExistsError(SchedulerError):
    """Raised when trying to create a schedule that already exists."""


class ScheduleConflictError(SchedulerError):
    """Raised when schedule operation conflicts with existing state.

    For example, trying to delete a schedule group that still has schedules.
    """


# ============================================================================
# SQS Queue Errors
# ============================================================================


class QueueError(AWSOperationError):
    """Base exception for SQS queue operations."""


class MessageProcessingError(QueueError):
    """Raised when processing an SQS message fails.

    This includes JSON parsing errors, validation errors, and business logic errors.
    """


class QueueNotFoundError(QueueError):
    """Raised when an SQS queue does not exist."""


class MessageSendError(QueueError):
    """Raised when sending a message to SQS fails."""


# ============================================================================
# Database Errors
# ============================================================================


class DatabaseError(EchoError):
    """Base exception for database operations."""


class CampaignNotFoundError(DatabaseError):
    """Raised when a campaign is not found in the database."""


class CampaignAlreadyExistsError(DatabaseError):
    """Raised when trying to create a campaign that already exists."""


# ============================================================================
# Business Logic Errors
# ============================================================================


class ValidationError(EchoError):
    """Raised when data validation fails."""


class CampaignValidationError(ValidationError):
    """Raised when campaign data validation fails."""


class ScheduleValidationError(ValidationError):
    """Raised when schedule configuration is invalid."""


# ============================================================================
# Utility Functions
# ============================================================================


def is_retryable_error(error: Exception) -> bool:
    """Determine if an error should trigger a retry.

    Args:
        error: The exception to evaluate

    Returns:
        bool: True if the operation should be retried, False otherwise
    """
    # Retryable AWS errors
    if isinstance(error, AWSThrottlingError):
        return True

    # Check for common retryable AWS error codes
    if isinstance(error, AWSOperationError) and error.aws_error_code:
        retryable_codes = {
            "ThrottlingException",
            "TooManyRequestsException",
            "ServiceUnavailable",
            "InternalServerError",
            "RequestTimeout",
            "ServiceException",
        }
        if error.aws_error_code in retryable_codes:
            return True

    # Network-related errors are retryable
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True

    # Other errors are not retryable
    return False


def is_not_found_error(error: Exception) -> bool:
    """Determine if an error indicates a resource was not found.

    Args:
        error: The exception to evaluate

    Returns:
        bool: True if the error indicates a not-found condition
    """
    return isinstance(
        error,
        (
            ScheduleNotFoundError,
            ScheduleGroupNotFoundError,
            CampaignNotFoundError,
            QueueNotFoundError,
        ),
    )


def extract_aws_error_code(error: Exception) -> str | None:
    """Extract AWS error code from boto3 exception.

    Args:
        error: The exception (typically from boto3)

    Returns:
        str | None: The AWS error code, or None if not available
    """
    # boto3 exceptions have an 'Error' dict with 'Code' key
    if hasattr(error, "response") and isinstance(error.response, dict):
        return error.response.get("Error", {}).get("Code")
    return None
