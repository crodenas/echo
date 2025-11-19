"""Basic routes for the Echo application."""

from typing import Union
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def read_root():
    """Root endpoint returning a simple greeting."""
    return {"Hello": "World"}


@router.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    """
    Get item details by ID.

    Args:
        item_id: The ID of the item to retrieve
        q: Optional query parameter

    Returns:
        Dict containing item_id and query parameter
    """
    return {"item_id": item_id, "q": q}
