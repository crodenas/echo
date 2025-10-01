"module"

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


class BackgroundSchedulerFactory:
    "class"

    @staticmethod
    def create_scheduler(name: str) -> BackgroundScheduler:
        "method"
        jobstores = {
            "default": SQLAlchemyJobStore(url=f"sqlite:///scheduler_{name}.sqlite")
        }
        return BackgroundScheduler(jobstores=jobstores)
