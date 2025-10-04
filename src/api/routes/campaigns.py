"""Campaign routes for the Echo application."""

from typing import List
from fastapi import APIRouter, HTTPException

from campaign import list_campaigns, add_campaign, update_campaign, get_campaign
from models import Campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/", response_model=List[Campaign])
async def get_campaigns():
    """
    Get all campaigns.

    Returns:
        List of all campaigns
    """
    return list_campaigns()


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
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return campaign


@router.post("/", response_model=Campaign)
async def create_campaign(campaign: Campaign):
    """
    Create a new campaign.

    Args:
        campaign: The campaign data to create

    Returns:
        The created campaign with assigned ID
    """
    return add_campaign(campaign)


@router.put("/{campaign_id}", response_model=Campaign)
async def update_campaign_by_id(campaign_id: int, campaign: Campaign):
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
    # Ensure ID in path and body match
    campaign.id = campaign_id
    updated = update_campaign(campaign)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return updated
