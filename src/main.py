"""Main module for the Echo application.

Initializes FastAPI application, sets up routing, and starts background SQS
consumers using the asynchronous consumer implementation.
"""

from fastapi import FastAPI

from api.routes.basic import router as basic_router
from api.routes.campaigns import router as campaigns_router
from core.lifecycle import lifespan

app = FastAPI(
    title="Echo API",
    description="Campaign Management API for automated reviews",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(basic_router)
app.include_router(campaigns_router)
