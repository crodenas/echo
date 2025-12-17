"""Campaign routes for the Echo application."""

from typing import List

from fastapi import APIRouter, HTTPException

from core.models import Campaign, CampaignCreate, CampaignUpdate
from services import campaign_service

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/", response_model=List[Campaign])
async def get_campaigns():
    """
    Get all campaigns.

    Returns:
        List of all campaigns
    """
    return campaign_service.list_campaigns()


@router.get("/{campaign_id}", response_model=Campaign)
async def get_campaign_by_id_route(campaign_id: int):
    """
    Get campaign by ID.

    Args:
        campaign_id: The ID of the campaign to retrieve

    Returns:
        Campaign details

    Raises:
        HTTPException: If campaign is not found
    """
    campaign = await campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return campaign


@router.post("/", response_model=Campaign)
async def create_campaign(campaign: CampaignCreate):
    """
    Create a new campaign.

    Args:
        campaign: The campaign data to create

    Returns:
        The created campaign with assigned ID
    """
    # Convert to Campaign with id=None for creation
    campaign_obj = Campaign(
        name=campaign.name,
        campaign_schedule=campaign.campaign_schedule,
        cycle_schedule=campaign.cycle_schedule,
        description=campaign.description,
        max_events=campaign.max_events,
        conn_string=campaign.conn_string,
        id=None,
    )
    return await campaign_service.create_campaign(campaign_obj)


@router.put("/{campaign_id}", response_model=Campaign)
async def update_campaign_by_id(campaign_id: int, campaign: CampaignUpdate):
    """
    Update an existing campaign.

    Args:
        campaign_id: The ID of the campaign to update
        campaign: The updated campaign data

    Returns:
        The updated campaign

    Raises:
        HTTPException: If campaign is not found
    """
    # Convert to Campaign with the provided id
    campaign_obj = Campaign(
        name=campaign.name,
        campaign_schedule=campaign.campaign_schedule,
        cycle_schedule=campaign.cycle_schedule,
        description=campaign.description,
        max_events=campaign.max_events,
        conn_string=campaign.conn_string,
        id=campaign_id,
    )
    updated = await campaign_service.update_campaign(campaign_obj)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return updated


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign_by_id(campaign_id: int):
    """
    Delete a campaign by ID.

    Args:
        campaign_id: The ID of the campaign to delete

    Raises:
        HTTPException: If campaign is not found
    """
    campaign = await campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    await campaign_service.delete_campaign(campaign_id)
