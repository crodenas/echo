"module"

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler


class BackgroundSchedulerFactory:
    "class"

    @staticmethod
    def create_scheduler(name: str) -> BackgroundScheduler:
        "method"
        jobstores = {
            "default": SQLAlchemyJobStore(url=f"sqlite:///scheduler_{name}.sqlite")
        }
        return BackgroundScheduler(jobstores=jobstores)
