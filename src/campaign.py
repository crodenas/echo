"module"

from typing import List

from sqlalchemy.orm import sessionmaker

from data.db_engine import echo_engine
from data.models import CampaignModel
from models import Campaign


def list_campaigns() -> List[Campaign]:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        return session.query(CampaignModel).all()


def create_campaign(campaign: Campaign) -> Campaign:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = CampaignModel(
            name=campaign.name, description=campaign.description
        )
        session.add(campaign_model)
        session.commit()
        session.refresh(campaign_model)
        return Campaign(
            id=campaign_model.id,
            name=campaign_model.name,
            description=campaign_model.description,
        )


# # infrastructure/mappers.py
# def to_domain(model: UserModel) -> User:
#     return User(id=model.id, email=model.email, name=model.name)


# def to_model(user: User) -> UserModel:
#     return UserModel(id=user.id, email=user.email, name=user.name)
