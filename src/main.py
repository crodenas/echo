"""Main module for the Echo application.

Initializes FastAPI application, sets up routing, and starts background SQS
consumers using the asynchronous consumer implementation.
"""

import asyncio

# # Ensure this 'src' directory is on sys.path so top-level imports like 'api', 'aws'
# # work when running without PYTHONPATH=src.
# _CURRENT_DIR = os.path.dirname(__file__)
# if _CURRENT_DIR not in sys.path:
#     sys.path.insert(0, _CURRENT_DIR)

from fastapi import FastAPI

from api.routes.basic import router as basic_router
from api.routes.campaigns import router as campaigns_router
from libs.aws.utils import validate_credentials
from utils.queue_watcher import create_sqs_consumer
from core import config
from core.scheduler import queue_1_handler

# Validate AWS credentials on import
# I don't like this.  Consider removing it.
validate_credentials()

app = FastAPI(
    title="Echo API",
    description="Campaign Management API for automated reviews",
    version="0.1.0",
)

# Include routers
app.include_router(basic_router)
app.include_router(campaigns_router)


# ---------------------------------------------------------------------------
# Asynchronous SQS Consumers
# ---------------------------------------------------------------------------
_consumers = []  # SQSConsumer instances
_consumer_tasks: list[asyncio.Task] = []  # Associated asyncio tasks


@app.on_event("startup")
async def _startup_consumers() -> None:
    """Create and start SQS consumers as background asyncio tasks."""
    consumer1 = create_sqs_consumer(config.QUEUE_1_URL, max_messages=5)
    # consumer2 = create_sqs_consumer(config.QUEUE_2_URL, max_messages=5)
    _consumers.extend([consumer1])
    _consumer_tasks.append(asyncio.create_task(consumer1.start_async(queue_1_handler)))
    # _consumer_tasks.append(asyncio.create_task(consumer2.start_async(queue_1_handler)))
    print("SQS consumers started (async).")


@app.on_event("shutdown")
async def _shutdown_consumers() -> None:
    """Signal consumers to stop and cancel running tasks."""
    for consumer in _consumers:
        consumer.stop()
    for task in _consumer_tasks:
        task.cancel()
    await asyncio.gather(*_consumer_tasks, return_exceptions=True)
    print("SQS consumers stopped.")
