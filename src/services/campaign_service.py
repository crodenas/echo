"""Campaign service module.

Handles all campaign-related business logic including CRUD operations
and coordination with AWS EventBridge scheduler.
"""

from typing import List

from sqlalchemy.orm import sessionmaker

from core.models import Campaign
from core.scheduler import (
    create_campaign_schedule,
    create_schedule_group,
    delete_schedule_group,
    list_schedules,
    update_campaign_schedule,
)
from db.db_engine import echo_engine
from db.schemas import CampaignSchema


async def create_campaign(campaign: Campaign) -> Campaign:
    """Create a new campaign with associated AWS EventBridge schedules.

    Args:
        campaign: Campaign domain model to create

    Returns:
        Created campaign with generated ID

    Raises:
        Exception: If AWS schedule creation fails (transaction will be rolled back)
    """
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = to_schema(campaign)
        session.add(campaign_model)
        session.flush()  # Assign ID without committing

        # Update campaign with the generated ID
        new_campaign = to_domain(campaign_model)

        try:
            # Create schedule group
            await create_schedule_group(campaign=new_campaign)
            # Create campaign schedule
            await create_campaign_schedule(campaign=new_campaign)
            session.commit()  # Commit only after AWS operations succeed
        except Exception as e:
            session.rollback()  # Rollback if AWS fails
            raise e

        return new_campaign


async def update_campaign(campaign: Campaign) -> Campaign | None:
    """Update an existing campaign and its AWS EventBridge schedules.

    Args:
        campaign: Campaign domain model with updated data

    Returns:
        Updated campaign or None if not found

    Raises:
        Exception: If AWS schedule update fails (transaction will be rolled back)
    """
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = to_schema(campaign)
        session.merge(campaign_model)

        try:
            await update_campaign_schedule(campaign=to_domain(campaign_model))
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

        return to_domain(campaign_model)


async def delete_campaign(campaign_id: int) -> None:
    """Delete a campaign and its associated AWS EventBridge schedule group.

    Args:
        campaign_id: ID of the campaign to delete
    """
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = session.get(CampaignSchema, campaign_id)
        if campaign_model:
            # Delete campaign schedule group (includes all schedules)
            await delete_schedule_group(campaign=to_domain(campaign_model))
            session.delete(campaign_model)
            session.commit()


async def get_campaign(campaign_id: int) -> Campaign | None:
    """Retrieve a campaign by ID and list its schedules.

    Args:
        campaign_id: ID of the campaign to retrieve

    Returns:
        Campaign domain model or None if not found
    """
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = session.get(CampaignSchema, campaign_id)
        campaign_domain = to_domain(campaign_model) if campaign_model else None

        if campaign_domain:
            # List schedules for the campaign
            schedules = await list_schedules(campaign=campaign_domain)
            print(f"Schedules for campaign {campaign_id}:")
            for schedule in schedules:
                print(f"- {schedule.name}: {schedule.schedule_expression}")

        return campaign_domain


def list_campaigns() -> List[Campaign]:
    """Retrieve all campaigns.

    Returns:
        List of all campaign domain models
    """
    with sessionmaker(bind=echo_engine)() as session:
        campaign_models = session.query(CampaignSchema).all()
    return [to_domain(campaign_model) for campaign_model in campaign_models]


# Domain/Schema conversion utilities
def to_domain(model: CampaignSchema) -> Campaign:
    """Convert database schema model to domain model.

    Args:
        model: SQLAlchemy campaign schema

    Returns:
        Campaign domain model
    """
    return Campaign(
        id=model.id,
        name=model.name,
        description=model.description,
        campaign_schedule=model.campaign_schedule,
        cycle_schedule=model.cycle_schedule,
        max_events=model.max_events,
        conn_string=model.conn_string,
    )


def to_schema(campaign: Campaign) -> CampaignSchema:
    """Convert domain model to database schema model.

    Args:
        campaign: Campaign domain model

    Returns:
        SQLAlchemy campaign schema
    """
    return CampaignSchema(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        campaign_schedule=campaign.campaign_schedule,
        cycle_schedule=campaign.cycle_schedule,
        max_events=campaign.max_events,
        conn_string=campaign.conn_string,
    )
