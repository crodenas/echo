"""Basic routes for the Echo application."""

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.models import Campaign, CampaignCreate, CampaignUpdate
from services import campaign_service

router = APIRouter(prefix="/campaigns")
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root(request: Request):
    """Root endpoint returning a simple greeting."""
    return templates.TemplateResponse(
        request, "index.html", {"message": "Hello World!"}
    )


@router.get("/create", response_class=HTMLResponse, include_in_schema=False)
async def create_campaign(request: Request):
    """Create a new campaign."""
    return templates.TemplateResponse(request, "create.html")


@router.post("/create", include_in_schema=False)
async def create_campaign_post(
    name: str = Form(...),
    description: str = Form(""),
    campaign_schedule: str = Form(...),
    cycle_schedule: str = Form(...),
    max_events: int = Form(...),
    conn_string: str | None = Form(None),
):
    """Create a new campaign from form data."""
    campaign = CampaignCreate(
        name=name,
        description=description,
        campaign_schedule=campaign_schedule,
        cycle_schedule=cycle_schedule,
        max_events=max_events,
        conn_string=conn_string,
    )
    campaign_obj = Campaign(**campaign.model_dump(), id=None)
    await campaign_service.create_campaign(campaign_obj)
    return RedirectResponse(url="/campaigns/list", status_code=303)


@router.get("/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_campaign(request: Request, campaign_id: int):
    """Delete a campaign."""
    campaign = await campaign_service.get_campaign(campaign_id)
    return templates.TemplateResponse(request, "delete.html", {"campaign": campaign})


@router.post("/delete", include_in_schema=False)
async def delete_campaign_post(campaign_id: int = Form(...)):
    """Delete a campaign from form data."""
    campaign = await campaign_service.get_campaign(campaign_id)
    if campaign:
        await campaign_service.delete_campaign(campaign_id)
    return RedirectResponse(url="/campaigns/list", status_code=303)


@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_campaigns(request: Request):
    """List all campaigns."""
    campaigns = campaign_service.list_campaigns()
    return templates.TemplateResponse(request, "list.html", {"campaigns": campaigns})


@router.get("/show", response_class=HTMLResponse, include_in_schema=False)
async def show_campaign(request: Request, campaign_id: int):
    """Show a campaign."""
    campaign = await campaign_service.get_campaign(campaign_id)
    return templates.TemplateResponse(request, "show.html", {"campaign": campaign})


@router.get("/update", response_class=HTMLResponse, include_in_schema=False)
async def update_campaign(request: Request, campaign_id: int):
    """Update a campaign."""
    campaign = await campaign_service.get_campaign(campaign_id)
    return templates.TemplateResponse(request, "update.html", {"campaign": campaign})


@router.post("/update", include_in_schema=False)
async def update_campaign_post(
    campaign_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    campaign_schedule: str = Form(...),
    cycle_schedule: str = Form(...),
    max_events: int = Form(...),
    conn_string: str | None = Form(None),
):
    """Update a campaign from form data."""
    campaign = CampaignUpdate(
        name=name,
        description=description,
        campaign_schedule=campaign_schedule,
        cycle_schedule=cycle_schedule,
        max_events=max_events,
        conn_string=conn_string,
    )
    campaign_obj = Campaign(**campaign.model_dump(), id=campaign_id)
    await campaign_service.update_campaign(campaign_obj)
    return RedirectResponse(
        url=f"/campaigns/show?campaign_id={campaign_id}", status_code=303
    )
