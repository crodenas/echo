"module"

import time
import asyncio
import inspect
from typing import Callable, Any

from aws import sqs


class SQSConsumer:
    "class"

    def __init__(self, queue_url: str, max_messages: int = 10) -> None:
        self.queue_url = queue_url
        self.max_messages = max_messages
        self.running = False

    def start(self, handler: Callable) -> None:
        """Start consuming messages synchronously in a blocking loop."""
        self.running = True
        while self.running:
            try:
                messages = sqs.receive_message(
                    queue_url=self.queue_url,
                    max_number_of_messages=self.max_messages,
                    wait_time_seconds=20,
                )
                for message in messages:
                    try:
                        handler(message)
                        # Delete after successful processing (uncomment when ready)
                        # sqs.delete_message(
                        #     queue_url=self.queue_url,
                        #     receipt_handle=message.receipt_handle,
                        # )
                    except Exception as e:
                        print(f"Error processing message: {e}")
            except Exception as e:
                print(f"Error receiving messages: {e}")
                time.sleep(5)  # Back off on errors

    async def start_async(self, handler: Callable[[Any], Any]) -> None:
        """Start consuming messages asynchronously.

        The underlying boto3 SQS client is synchronous; calls are offloaded
        to a thread using ``asyncio.to_thread``. Handlers may be synchronous
        or asynchronous (coroutines). To stop the loop call ``stop()`` or
        cancel the task running this method.
        """
        self.running = True
        try:
            while self.running:
                try:
                    messages = await asyncio.to_thread(
                        sqs.receive_message,
                        queue_url=self.queue_url,
                        max_number_of_messages=self.max_messages,
                        wait_time_seconds=20,
                    )
                    for message in messages:
                        try:
                            result = handler(message)
                            if inspect.iscoroutine(result):
                                await result
                            # Delete after successful processing (uncomment when ready)
                            # await asyncio.to_thread(
                            #     sqs.delete_message,
                            #     queue_url=self.queue_url,
                            #     receipt_handle=message.receipt_handle,
                            # )
                        except Exception as e:
                            print(f"Error processing message asynchronously: {e}")
                except Exception as e:
                    print(f"Error receiving messages asynchronously: {e}")
                    await asyncio.sleep(5)  # Back off on errors
        except asyncio.CancelledError:
            # Graceful cancellation
            pass
        finally:
            self.running = False

    def stop(self) -> None:
        """Signal the consumer loop to stop."""
        self.running = False


def create_sqs_consumer(queue_url: str, max_messages: int = 10) -> SQSConsumer:
    "function"
    return SQSConsumer(queue_url=queue_url, max_messages=max_messages)
