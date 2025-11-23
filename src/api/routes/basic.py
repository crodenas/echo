"""Basic routes for the Echo application."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from core import campaign as lib_campaign

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root(request: Request):
    """Root endpoint returning a simple greeting."""
    return templates.TemplateResponse(
        "index.html", {"request": request, "message": "Hello World!"}
    )


@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_campaigns(request: Request):
    """List all campaigns."""
    campaigns = lib_campaign.list_campaigns()
    return templates.TemplateResponse(
        "list.html", {"request": request, "campaigns": campaigns}
    )
