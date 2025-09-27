"module"

from typing import Optional
from data import db
from models import Worker


employee_db = db.read_json_db("data/WorkerObjects.json")


def get_by_system_id(system_id: str) -> Optional[Worker]:
    """Get a Worker by their SystemId."""
    for emp in employee_db:
        if emp["SystemId"] == system_id:
            return Worker(**emp)
    return None


__all__ = ["Worker", "get_by_system_id"]
