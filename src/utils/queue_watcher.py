"""SQS Queue consumer for processing messages.

This module provides an SQS consumer that polls queues for messages and
processes them using configured handlers. Includes error handling, retry
logic with exponential backoff, and structured logging.
"""

import asyncio
import inspect
import time
from typing import Any, Callable

from aws_v2 import sqs

from core.exceptions import (
    AWSCredentialsError,
    MessageProcessingError,
    QueueError,
    extract_aws_error_code,
    is_retryable_error,
)
from core.logger import get_logger

logger = get_logger(__name__)


class SQSConsumer:
    """SQS queue consumer for processing messages with error handling.

    Polls an SQS queue for messages and processes them using a provided handler.
    Supports both synchronous and asynchronous handlers with automatic message
    deletion on successful processing.
    """

    def __init__(
        self,
        queue_url: str,
        max_messages: int = 10,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        backoff_multiplier: float = 2.0,
    ) -> None:
        """Initialize SQS consumer.

        Args:
            queue_url: The SQS queue URL to consume from
            max_messages: Maximum messages to receive per poll (1-10)
            initial_backoff: Initial backoff time in seconds for errors
            max_backoff: Maximum backoff time in seconds
            backoff_multiplier: Multiplier for exponential backoff
        """
        self.queue_url = queue_url
        self.max_messages = max_messages
        self.running = False
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier
        self._current_backoff = initial_backoff

        # Extract queue name from URL for logging
        self.queue_name = queue_url.split("/")[-1] if queue_url else "unknown"

        logger.info(
            f"Initialized SQS consumer for queue {self.queue_name}",
            extra={
                "queue_url": queue_url,
                "queue_name": self.queue_name,
                "max_messages": max_messages,
            },
        )

    def _reset_backoff(self) -> None:
        """Reset backoff to initial value after successful operation."""
        self._current_backoff = self.initial_backoff

    def _increase_backoff(self) -> float:
        """Increase backoff time exponentially and return current value."""
        current = self._current_backoff
        self._current_backoff = min(
            self._current_backoff * self.backoff_multiplier,
            self.max_backoff,
        )
        return current

    def _handle_receive_error(self, error: Exception) -> float:
        """Handle errors when receiving messages from SQS.

        Args:
            error: The exception that occurred

        Returns:
            float: Backoff time in seconds before retry
        """
        error_code = extract_aws_error_code(error)

        # Check for credential errors
        if error_code in ("InvalidClientTokenId", "SignatureDoesNotMatch", "AccessDenied"):
            logger.critical(
                f"AWS credentials error for queue {self.queue_name}",
                extra={
                    "queue_name": self.queue_name,
                    "queue_url": self.queue_url,
                    "error_code": error_code,
                    "error": str(error),
                },
            )
            # For credential errors, use max backoff to avoid hammering AWS
            return self.max_backoff

        # Check for retryable errors
        if is_retryable_error(error):
            backoff = self._increase_backoff()
            logger.warning(
                f"Retryable error receiving messages from queue {self.queue_name}",
                extra={
                    "queue_name": self.queue_name,
                    "queue_url": self.queue_url,
                    "error_code": error_code,
                    "error": str(error),
                    "backoff_seconds": backoff,
                },
            )
            return backoff

        # Non-retryable errors
        backoff = self._increase_backoff()
        logger.error(
            f"Error receiving messages from queue {self.queue_name}",
            extra={
                "queue_name": self.queue_name,
                "queue_url": self.queue_url,
                "error_code": error_code,
                "error_type": type(error).__name__,
                "error": str(error),
                "backoff_seconds": backoff,
            },
        )
        return backoff

    def _handle_processing_error(
        self, error: Exception, message_id: str | None = None
    ) -> None:
        """Handle errors when processing individual messages.

        Args:
            error: The exception that occurred
            message_id: The message ID if available
        """
        context = {
            "queue_name": self.queue_name,
            "queue_url": self.queue_url,
        }
        if message_id:
            context["message_id"] = message_id

        # Categorize error types
        if isinstance(error, MessageProcessingError):
            logger.error(
                f"Message processing error in queue {self.queue_name}",
                extra={
                    **context,
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
            )
        elif isinstance(error, QueueError):
            logger.error(
                f"Queue operation error in queue {self.queue_name}",
                extra={
                    **context,
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
            )
        else:
            logger.error(
                f"Unexpected error processing message in queue {self.queue_name}",
                extra={
                    **context,
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
                exc_info=True,
            )

    def start(self, handler: Callable) -> None:
        """Start consuming messages synchronously in a blocking loop.

        Args:
            handler: Callable to process each message (synchronous)
        """
        self.running = True
        logger.info(
            f"Starting synchronous consumer for queue {self.queue_name}",
            extra={"queue_name": self.queue_name, "queue_url": self.queue_url},
        )

        while self.running:
            try:
                messages = sqs.receive_message(
                    queue_url=self.queue_url,
                    max_number_of_messages=self.max_messages,
                    wait_time_seconds=5,
                )

                # Reset backoff on successful receive
                if messages:
                    self._reset_backoff()
                    logger.debug(
                        f"Received {len(messages)} messages from queue {self.queue_name}",
                        extra={
                            "queue_name": self.queue_name,
                            "message_count": len(messages),
                        },
                    )

                for message in messages:
                    try:
                        handler(message)
                        # Delete after successful processing
                        sqs.delete_message(
                            queue_url=self.queue_url,
                            receipt_handle=message.receipt_handle,
                        )
                        logger.debug(
                            f"Successfully processed and deleted message from queue {self.queue_name}",
                            extra={
                                "queue_name": self.queue_name,
                                "message_id": message.message_id,
                            },
                        )
                    except Exception as e:
                        self._handle_processing_error(e, message.message_id)
                        # Message will remain in queue for retry or DLQ

            except Exception as e:
                backoff = self._handle_receive_error(e)
                time.sleep(backoff)

        logger.info(
            f"Stopped synchronous consumer for queue {self.queue_name}",
            extra={"queue_name": self.queue_name},
        )

    async def start_async(self, handler: Callable[[Any], Any]) -> None:
        """Start consuming messages asynchronously.

        The underlying boto3 SQS client is synchronous; calls are offloaded
        to a thread using ``asyncio.to_thread``. Handlers may be synchronous
        or asynchronous (coroutines). To stop the loop call ``stop()`` or
        cancel the task running this method.

        Args:
            handler: Callable to process each message (sync or async)
        """
        self.running = True
        logger.info(
            f"Starting asynchronous consumer for queue {self.queue_name}",
            extra={"queue_name": self.queue_name, "queue_url": self.queue_url},
        )

        try:
            while self.running:
                try:
                    messages = await asyncio.to_thread(
                        sqs.receive_message,
                        queue_url=self.queue_url,
                        max_number_of_messages=self.max_messages,
                        wait_time_seconds=5,
                    )

                    # Reset backoff on successful receive
                    if messages:
                        self._reset_backoff()
                        logger.debug(
                            f"Received {len(messages)} messages from queue {self.queue_name}",
                            extra={
                                "queue_name": self.queue_name,
                                "message_count": len(messages),
                            },
                        )

                    for message in messages:
                        try:
                            result = handler(message)
                            if inspect.iscoroutine(result):
                                await result

                            # Delete after successful processing
                            await asyncio.to_thread(
                                sqs.delete_message,
                                queue_url=self.queue_url,
                                receipt_handle=message.receipt_handle,
                            )
                            logger.debug(
                                f"Successfully processed and deleted message from queue {self.queue_name}",
                                extra={
                                    "queue_name": self.queue_name,
                                    "message_id": message.message_id,
                                },
                            )
                        except Exception as e:
                            self._handle_processing_error(e, message.message_id)
                            # Message will remain in queue for retry or DLQ

                except Exception as e:
                    backoff = self._handle_receive_error(e)
                    await asyncio.sleep(backoff)

        except asyncio.CancelledError:
            logger.info(
                f"Async consumer cancelled for queue {self.queue_name}",
                extra={"queue_name": self.queue_name},
            )
        finally:
            self.running = False
            logger.info(
                f"Stopped asynchronous consumer for queue {self.queue_name}",
                extra={"queue_name": self.queue_name},
            )

    def stop(self) -> None:
        """Signal the consumer loop to stop."""
        logger.info(
            f"Stopping consumer for queue {self.queue_name}",
            extra={"queue_name": self.queue_name},
        )
        self.running = False


def create_sqs_consumer(
    queue_url: str,
    max_messages: int = 10,
    initial_backoff: float = 1.0,
    max_backoff: float = 60.0,
    backoff_multiplier: float = 2.0,
) -> SQSConsumer:
    """Create an SQS consumer instance.

    Args:
        queue_url: The SQS queue URL to consume from
        max_messages: Maximum messages to receive per poll (1-10)
        initial_backoff: Initial backoff time in seconds for errors
        max_backoff: Maximum backoff time in seconds
        backoff_multiplier: Multiplier for exponential backoff

    Returns:
        SQSConsumer: Configured consumer instance
    """
    return SQSConsumer(
        queue_url=queue_url,
        max_messages=max_messages,
        initial_backoff=initial_backoff,
        max_backoff=max_backoff,
        backoff_multiplier=backoff_multiplier,
    )
