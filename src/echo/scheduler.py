"module"

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from echo.models import Campaign


class CampaignSchedulerFactory:
    "class"

    @staticmethod
    def create_scheduler(campaign: Campaign) -> BackgroundScheduler:
        "method"
        jobstores = {
            "default": SQLAlchemyJobStore(
                url=f"sqlite:///data/schedules/campaign_{campaign.id}.sqlite"
            )
        }
        return BackgroundScheduler(jobstores=jobstores)
