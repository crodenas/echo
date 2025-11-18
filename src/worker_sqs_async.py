"module"

import asyncio
import json
import signal
from typing import Any

import config
import campaign as campaign_module
from queue_watcher import create_sqs_consumer


# Handlers -------------------------------------------------
async def queue_1_handler(message: Any) -> None:
    """Process messages from Queue 1 asynchronously."""
    print(f"[Queue1] Raw: {message.body}")
    try:
        payload = json.loads(message.body)
    except json.JSONDecodeError:
        print("[Queue1] Invalid JSON body")
        return
    campaign_id = payload.get("campaign_id")
    if campaign_id is None:
        print("[Queue1] Missing campaign_id")
        return
    campaign = await campaign_module.get_campaign(campaign_id)
    if campaign:
        print(f"[Queue1] Retrieved campaign {campaign.id} : {campaign.name}")
    else:
        print(f"[Queue1] Campaign {campaign_id} not found")


async def queue_2_handler(message: Any) -> None:
    """Process messages from Queue 2 asynchronously (placeholder)."""
    print(f"[Queue2] Raw: {message.body}")


# Runner ---------------------------------------------------
async def run_consumers() -> None:
    consumer1 = create_sqs_consumer(config.QUEUE_1_URL, max_messages=5)
    consumer2 = create_sqs_consumer(config.QUEUE_2_URL, max_messages=5)

    task1 = asyncio.create_task(consumer1.start_async(queue_1_handler))
    task2 = asyncio.create_task(consumer2.start_async(queue_2_handler))

    stop_event = asyncio.Event()

    def _handle_stop(*_: Any) -> None:
        print("\nReceived stop signal; shutting down consumers...")
        consumer1.stop()
        consumer2.stop()
        stop_event.set()

    # Register signals for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            asyncio.get_running_loop().add_signal_handler(sig, _handle_stop)
        except NotImplementedError:
            # Signal handlers may not be available (e.g., on Windows)
            pass

    # Wait until stop requested
    await stop_event.wait()

    # Cancel tasks if still running
    for t in (task1, task2):
        if not t.done():
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass

    print("Consumers stopped.")


async def main() -> None:
    await run_consumers()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt; exit.")
