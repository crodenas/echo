"module"

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from utils.queue_watcher import create_sqs_consumer
from core import config
from core.scheduler import queue_1_handler


# ---------------------------------------------------------------------------
# Asynchronous SQS Consumers
# ---------------------------------------------------------------------------
_consumers = []  # SQSConsumer instances
_consumer_tasks: list[asyncio.Task] = []  # Associated asyncio tasks


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifecycle event handler for the FastAPI application.

    This context manager handles startup and shutdown events:
    - On startup: Creates and starts SQS consumers as background asyncio tasks
    - On shutdown: Stops consumers and cancels running tasks gracefully

    Args:
        _app: The FastAPI application instance (unused but required by FastAPI)
    """
    # Startup: Create and start SQS consumers
    consumer1 = create_sqs_consumer(config.QUEUE_1_URL, max_messages=5)
    # consumer2 = create_sqs_consumer(config.QUEUE_2_URL, max_messages=5)
    _consumers.extend([consumer1])
    _consumer_tasks.append(asyncio.create_task(consumer1.start_async(queue_1_handler)))
    # _consumer_tasks.append(asyncio.create_task(consumer2.start_async(queue_1_handler)))
    print("SQS consumers started (async).")

    yield  # Application runs here

    # Shutdown: Stop consumers and cancel tasks
    for consumer in _consumers:
        consumer.stop()
    for task in _consumer_tasks:
        task.cancel()
    await asyncio.gather(*_consumer_tasks, return_exceptions=True)
    print("SQS consumers stopped.")
