"module"

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


def create_scheduler(name: str) -> BackgroundScheduler:
    "function"

    jobstores = {
        "default": SQLAlchemyJobStore(url=f"sqlite:///scheduler_{name}.sqlite")
    }
    return BackgroundScheduler(jobstores=jobstores)
