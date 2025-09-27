"module"

from data import db
from models import CampaignObject

campaign_db = db.read_json_db("data/CampaignObjects.json")


def get_campaign_objects() -> list[CampaignObject]:
    """Get all campaign objects from the database."""
    return [CampaignObject(**obj) for obj in campaign_db]
