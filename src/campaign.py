"module"

from typing import List

from sqlalchemy.orm import sessionmaker

from db.db_engine import echo_engine
from db.schemas import CampaignSchema
from models import Campaign


def add_campaign(campaign: Campaign) -> Campaign:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = to_schema(campaign)
        session.add(campaign_model)
        session.commit()
        session.refresh(campaign_model)
        # Create schedule
        return to_domain(campaign_model)


def delete_campaign(campaign_id: int) -> None:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = session.get(CampaignSchema, campaign_id)
        if campaign_model:
            session.delete(campaign_model)
            session.commit()


def get_campaign(campaign_id: int) -> Campaign | None:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = session.get(CampaignSchema, campaign_id)
        return to_domain(campaign_model) if campaign_model else None


def list_campaigns() -> List[Campaign]:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_models = session.query(CampaignSchema).all()
    return [to_domain(campaign_model) for campaign_model in campaign_models]


def update_campaign(campaign: Campaign) -> Campaign | None:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = to_schema(campaign)
        session.merge(campaign_model)
        session.commit()
        # Update schedule
        return to_domain(campaign_model)


# Utilities
def to_domain(model: CampaignSchema) -> Campaign:
    "function"
    return Campaign(
        id=model.id,
        name=model.name,
        description=model.description,
        campaign_frequency=model.campaign_frequency,
        cycle_frequency=model.cycle_frequency,
        max_events=model.max_events,
    )


def to_schema(campaign: Campaign) -> CampaignSchema:
    "function"
    return CampaignSchema(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        campaign_frequency=campaign.campaign_frequency,
        cycle_frequency=campaign.cycle_frequency,
        max_events=campaign.max_events,
    )
