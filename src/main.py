"module"

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Union, List
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from campaign import list_campaigns
from scheduler import CampaignSchedulerFactory


@asynccontextmanager
async def lifespan(app: FastAPI):
    "context manager for app lifespan"
    start_schedulers()
    yield
    stop_schedulers()


app = FastAPI(lifespan=lifespan)
# Global variable to store schedulers so they can be accessed in shutdown event
schedulers: List[BackgroundScheduler] = []


@app.get("/")
async def read_root():
    "function"
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    "function"
    return {"item_id": item_id, "q": q}


def tick(name: str):
    "function"
    print(f"The time is: {datetime.now()} for {name}")


def start_schedulers():
    "function"
    global schedulers

    scheduler_factory = CampaignSchedulerFactory()

    # Get Campaigns
    campaigns = list_campaigns()

    # For each campaign, start each scheduler
    for campaign in campaigns:
        print(f"Scheduling campaign: {campaign.id}:{campaign.name}")
        scheduler = scheduler_factory.create_scheduler(campaign)
        schedulers.append(scheduler)
        scheduler.add_job(
            tick,
            trigger="cron",
            minute="*",
            args=[f"Campaign {campaign.name}"],
            id=f"tick_{campaign.id}",
            replace_existing=True,
        )
        scheduler.start()
    print(f"Started {len(schedulers)} schedulers")


def stop_schedulers():
    "function"
    global schedulers
    print("Shutting down schedulers...")
    for scheduler in schedulers:
        scheduler.shutdown()
    print("Schedulers shut down.")


# For backwards compatibility or when running as standalone script
def main():
    "function"
    start_schedulers()
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        stop_schedulers()


if __name__ == "__main__":
    main()
