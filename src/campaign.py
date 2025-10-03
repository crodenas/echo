"module"

from typing import List

from sqlalchemy.orm import sessionmaker

from data.db_engine import echo_engine
from data.models import CampaignModel
from models import Campaign


def list_campaigns() -> List[Campaign]:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_models = session.query(CampaignModel).all()
    return [to_domain(campaign_model) for campaign_model in campaign_models]


def create_campaign(campaign: Campaign) -> Campaign:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = CampaignModel(
            name=campaign.name,
            description=campaign.description,
        )
        session.add(campaign_model)
        session.commit()
        session.refresh(campaign_model)
        return to_domain(campaign_model)


def to_domain(model: CampaignModel) -> Campaign:
    "function"
    return Campaign(id=model.id, name=model.name, description=model.description)


def to_model(campaign: Campaign) -> CampaignModel:
    "function"
    return CampaignModel(
        id=campaign.id, name=campaign.name, description=campaign.description
    )
