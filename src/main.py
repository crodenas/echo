"""Main module for the Echo application.

Initializes FastAPI application, sets up routing, and manages application lifespan.
"""

from fastapi import FastAPI, APIRouter

from api.routes.basic import router as basic_router
from api.routes.campaigns import router as campaigns_router
from core.lifecycle import lifespan
from core.logger import setup_logging

# Initialize logging
setup_logging()

app = FastAPI(
    title="Echo API",
    description="Campaign Management API for automated reviews",
    version="0.1.0",
    lifespan=lifespan,
)

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")
api_router.include_router(campaigns_router)

# Include routers
app.include_router(basic_router)
app.include_router(api_router)
