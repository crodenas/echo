"module"

from typing import List

from sqlalchemy.orm import sessionmaker

from .db.db_engine import echo_engine
from .db.schemas import CampaignSchema
from .models import Campaign
from .scheduler import (
    create_campaign_schedule,
    create_schedule_group,
    delete_schedule_group,
    update_campaign_schedule,
    list_schedules,
)


async def create_campaign(campaign: Campaign) -> Campaign:
    "function"
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
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = to_schema(campaign)
        session.merge(campaign_model)
        # Update schedule
        try:
            await update_campaign_schedule(campaign=to_domain(campaign_model))
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        return to_domain(campaign_model)


async def delete_campaign(campaign_id: int) -> None:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = session.get(CampaignSchema, campaign_id)
        if campaign_model:
            # Delete campaign schedule group
            await delete_schedule_group(campaign=to_domain(campaign_model))
            session.delete(campaign_model)
            session.commit()


async def get_campaign(campaign_id: int) -> Campaign | None:
    "function"
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
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_models = session.query(CampaignSchema).all()
    return [to_domain(campaign_model) for campaign_model in campaign_models]


# Utilities
def to_domain(model: CampaignSchema) -> Campaign:
    "function"
    return Campaign(
        id=model.id,
        name=model.name,
        description=model.description,
        campaign_schedule=model.campaign_schedule,
        cycle_schedule=model.cycle_schedule,
        max_events=model.max_events,
    )


def to_schema(campaign: Campaign) -> CampaignSchema:
    "function"
    return CampaignSchema(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        campaign_schedule=campaign.campaign_schedule,
        cycle_schedule=campaign.cycle_schedule,
        max_events=campaign.max_events,
    )
