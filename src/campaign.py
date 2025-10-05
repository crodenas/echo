"module"

from typing import List

from sqlalchemy.orm import sessionmaker

from db.db_engine import echo_engine
from db.schemas import CampaignSchema
from models import Campaign


def list_campaigns() -> List[Campaign]:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_models = session.query(CampaignSchema).all()
    return [to_domain(campaign_model) for campaign_model in campaign_models]


def add_campaign(campaign: Campaign) -> Campaign:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = to_schema(campaign)
        session.add(campaign_model)
        session.commit()
        session.refresh(campaign_model)
        return to_domain(campaign_model)


def update_campaign(campaign: Campaign) -> Campaign | None:
    "function"
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = to_schema(campaign)
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
        campaign_model = to_schema(campaign)
        session.delete(campaign_model)
        session.commit()


# Utilities
def to_domain(model: CampaignSchema) -> Campaign:
    "function"
    cycle_schedule = deserialize_schedule(model.cycle_schedule)
    escalation_schedule = deserialize_schedule(model.escalation_schedule)

    return Campaign(
        id=model.id,
        name=model.name,
        description=model.description,
        cycle_schedule=cycle_schedule,
        escalation_schedule=escalation_schedule,
    )


def to_schema(campaign: Campaign) -> CampaignSchema:
    "function"
    return CampaignSchema(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        cycle_schedule=serialize_schedule(campaign.cycle_schedule),
        escalation_schedule=serialize_schedule(campaign.escalation_schedule),
    )


def serialize_schedule(schedule):
    "function"
    if schedule is None:
        return None

    result = {
        "type": schedule.__class__.__name__,
        "config": {k: v for k, v in schedule.__dict__.items()},
    }
    return result


def deserialize_schedule(schedule_dict):
    "function"
    from models import CronSchedule, IntervalSchedule, OneTimeSchedule

    if schedule_dict is None:
        return None

    schedule_type = schedule_dict.get("type")
    config = schedule_dict.get("config", {})

    if schedule_type == "CronSchedule":
        return CronSchedule(**config)
    elif schedule_type == "IntervalSchedule":
        return IntervalSchedule(**config)
    elif schedule_type == "OneTimeSchedule":
        return OneTimeSchedule(**config)
    else:
        return None
