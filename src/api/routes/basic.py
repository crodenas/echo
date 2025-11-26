"""Basic routes for the Echo application."""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core import campaign as lib_campaign
from core.models import Campaign, CampaignCreate, CampaignUpdate

router = APIRouter(prefix="/campaigns")
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root(request: Request):
    """Root endpoint returning a simple greeting."""
    return templates.TemplateResponse(
        "index.html", {"request": request, "message": "Hello World!"}
    )


@router.get("/create", response_class=HTMLResponse, include_in_schema=False)
async def create_campaign(request: Request):
    """Create a new campaign."""
    return templates.TemplateResponse("create.html", {"request": request})


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
    await lib_campaign.create_campaign(campaign_obj)
    return RedirectResponse(url="/campaigns/list", status_code=303)


@router.get("/delete", response_class=HTMLResponse, include_in_schema=False)
async def delete_campaign(request: Request, campaign_id: int):
    """Delete a campaign."""
    campaign = await lib_campaign.get_campaign(campaign_id)
    return templates.TemplateResponse(
        "delete.html", {"request": request, "campaign": campaign}
    )


@router.post("/delete", include_in_schema=False)
async def delete_campaign_post(campaign_id: int = Form(...)):
    """Delete a campaign from form data."""
    campaign = await lib_campaign.get_campaign(campaign_id)
    if campaign:
        await lib_campaign.delete_campaign(campaign_id)
    return RedirectResponse(url="/campaigns/list", status_code=303)


@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
async def list_campaigns(request: Request):
    """List all campaigns."""
    campaigns = lib_campaign.list_campaigns()
    return templates.TemplateResponse(
        "list.html", {"request": request, "campaigns": campaigns}
    )


@router.get("/show", response_class=HTMLResponse, include_in_schema=False)
async def show_campaign(request: Request, campaign_id: int):
    """Show a campaign."""
    campaign = await lib_campaign.get_campaign(campaign_id)
    return templates.TemplateResponse(
        "show.html", {"request": request, "campaign": campaign}
    )


@router.get("/update", response_class=HTMLResponse, include_in_schema=False)
async def update_campaign(request: Request, campaign_id: int):
    """Update a campaign."""
    campaign = await lib_campaign.get_campaign(campaign_id)
    return templates.TemplateResponse(
        "update.html", {"request": request, "campaign": campaign}
    )


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
    await lib_campaign.update_campaign(campaign_obj)
    return RedirectResponse(
        url=f"/campaigns/show?campaign_id={campaign_id}", status_code=303
    )
