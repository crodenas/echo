"""Main module for the Echo application.

This module initializes the FastAPI application and sets up routing and service dependencies.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes.basic import router as basic_router
from services.scheduler_service import SchedulerService


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Context manager for application lifespan.

    This handles starting and stopping schedulers when the app starts and shuts down.

    Args:
        _: The FastAPI application instance (unused but required by FastAPI)
    """
    scheduler_service = SchedulerService()
    scheduler_service.start()
    yield
    scheduler_service.stop()


app = FastAPI(
    title="Echo API",
    description="Campaign Management API for automated reviews",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(basic_router)
# Import all available routes
try:
    from api.routes.campaigns import router as campaigns_router

    app.include_router(campaigns_router)
except ImportError as e:
    print(f"Warning: Campaign routes could not be loaded - {e}")


# For backwards compatibility or when running as standalone script
def main():
    """
    Main function for running the scheduler service directly.

    This function is used when the module is run as a standalone script.
    It starts the schedulers and keeps the main thread alive until interrupted.
    """
    scheduler_service = SchedulerService()
    scheduler_service.start()
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler_service.stop()


if __name__ == "__main__":
    main()
