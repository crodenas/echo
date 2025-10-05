"module"

import os
from pathlib import Path

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from models import Campaign


class CampaignSchedulerFactory:
    "class"

    @staticmethod
    def create_scheduler(campaign: Campaign) -> BackgroundScheduler:
        "method"
        # Get the absolute path to the schedules directory
        project_root = Path(__file__).parent
        schedules_dir = project_root / "data" / "schedules"
        os.makedirs(schedules_dir, exist_ok=True)
        db_path = schedules_dir / f"campaign_{campaign.id}.sqlite"

        jobstores = {"default": SQLAlchemyJobStore(url=f"sqlite:///{db_path}")}
        return BackgroundScheduler(jobstores=jobstores)
