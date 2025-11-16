"module"

import time
from typing import Callable

from aws import sqs


class SQSConsumer:
    "class"

    def __init__(self, queue_url: str, max_messages: int = 10) -> None:
        self.queue_url = queue_url
        self.max_messages = max_messages
        self.running = False

    def start(self, handler: Callable) -> None:
        """Start consuming messages"""
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
                        # Delete after successful processing
                        # sqs.delete_message(
                        #     queue_url=self.queue_url,
                        #     receipt_handle=message.receipt_handle,
                        # )
                    except Exception as e:
                        print(f"Error processing message: {e}")
                        # Message will become visible again after visibility timeout
                        # TODO: Configure a DLQ

            except Exception as e:
                print(f"Error receiving messages: {e}")
                time.sleep(5)  # Back off on errors

    def stop(self) -> None:
        """Stop consuming messages"""
        self.running = False


def create_sqs_consumer(queue_url: str, max_messages: int = 10) -> SQSConsumer:
    "function"
    return SQSConsumer(queue_url=queue_url, max_messages=max_messages)
