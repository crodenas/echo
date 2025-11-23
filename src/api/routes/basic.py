"""Basic routes for the Echo application."""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core import campaign as lib_campaign
from core.models import Campaign, CampaignCreate, CampaignUpdate

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


@router.get("/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_campaign(request: Request, campaign_id: int):
    """Edit a campaign."""
    campaign = await lib_campaign.get_campaign(campaign_id)
    return templates.TemplateResponse(
        "edit.html", {"request": request, "campaign": campaign}
    )


@router.get("/create", response_class=HTMLResponse, include_in_schema=False)
async def create_campaign(request: Request):
    """Create a new campaign."""
    return templates.TemplateResponse("create.html", {"request": request})


@router.get("/view", response_class=HTMLResponse, include_in_schema=False)
async def view_campaign(request: Request, campaign_id: int):
    """View a campaign."""
    campaign = await lib_campaign.get_campaign(campaign_id)
    return templates.TemplateResponse(
        "view.html", {"request": request, "campaign": campaign}
    )


@router.post("/create", include_in_schema=False)
async def create_campaign_post(
    name: str = Form(...),
    description: str = Form(""),
    campaign_schedule: str = Form(...),
    cycle_schedule: str = Form(...),
    max_events: int = Form(...),
):
    """Create a new campaign from form data."""
    campaign = Campaign(
        name=name,
        description=description,
        campaign_schedule=campaign_schedule,
        cycle_schedule=cycle_schedule,
        max_events=max_events,
        id=None,
    )
    await lib_campaign.create_campaign(campaign)
    return RedirectResponse(url="/list", status_code=303)


@router.post("/edit", include_in_schema=False)
async def edit_campaign_post(
    campaign_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    campaign_schedule: str = Form(...),
    cycle_schedule: str = Form(...),
    max_events: int = Form(...),
):
    """Update a campaign from form data."""
    campaign = Campaign(
        name=name,
        description=description,
        campaign_schedule=campaign_schedule,
        cycle_schedule=cycle_schedule,
        max_events=max_events,
        id=campaign_id,
    )
    await lib_campaign.update_campaign(campaign)
    return RedirectResponse(url=f"/view?campaign_id={campaign_id}", status_code=303)
