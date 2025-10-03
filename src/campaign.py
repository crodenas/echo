"module"

from typing import List

from sqlalchemy.orm import sessionmaker

from data.db_engine import echo_engine
from data.models import CampaignSchema
from models import Campaign


def list_campaigns() -> List[Campaign]:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_models = session.query(CampaignSchema).all()
    return [to_domain(campaign_model) for campaign_model in campaign_models]


def add_campaign(campaign: Campaign) -> Campaign:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = CampaignSchema(
            name=campaign.name,
            description=campaign.description,
        )
        session.add(campaign_model)
        session.commit()
        session.refresh(campaign_model)
        return to_domain(campaign_model)


def update_campaign(campaign: Campaign) -> Campaign | None:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = to_model(campaign)
        session.merge(campaign_model)
        session.commit()
        return to_domain(campaign_model)


def get_campaign(campaign_id: int) -> Campaign | None:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = session.get(CampaignSchema, campaign_id)
        return to_domain(campaign_model) if campaign_model else None


def delete_campaign(campaign: Campaign) -> None:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = to_model(campaign)
        session.delete(campaign_model)
        session.commit()


# Utilities
def to_domain(model: CampaignSchema) -> Campaign:
    "function"
    return Campaign(id=model.id, name=model.name, description=model.description)


def to_model(campaign: Campaign) -> CampaignSchema:
    "function"
    return CampaignSchema(
        id=campaign.id, name=campaign.name, description=campaign.description
    )
