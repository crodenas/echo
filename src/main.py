"""Main module for the Echo application.

This module initializes the FastAPI application and sets up routing and service dependencies.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.routes.basic import router as basic_router
from aws.utils import validate_credentials


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    try:
        validate_credentials()
        print("AWS credentials validated successfully.")
    except Exception as e:
        print(f"Warning: {e}")
        # Optionally, you can raise to prevent startup
        # raise e
    yield
    # Shutdown (add cleanup code here if needed)


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
