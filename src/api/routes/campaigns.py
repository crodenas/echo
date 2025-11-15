"""Campaign routes for the Echo application."""

from typing import List
from fastapi import APIRouter, HTTPException

import campaign as lib_campaign

from models import Campaign, CampaignCreate, CampaignUpdate

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/", response_model=List[Campaign])
async def get_campaigns():
    """
    Get all campaigns.

    Returns:
        List of all campaigns
    """
    return lib_campaign.list_campaigns()


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
    campaign = await lib_campaign.get_campaign(campaign_id)
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
        id=None,
    )
    return await lib_campaign.create_campaign(campaign_obj)


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
        id=campaign_id,
    )
    updated = await lib_campaign.update_campaign(campaign_obj)
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
    campaign = await lib_campaign.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    await lib_campaign.delete_campaign(campaign_id)
