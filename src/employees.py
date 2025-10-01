"module"

from typing import Optional

from data import db
from models import Employee

employee_db = db.read_json_db("data/Employees.json")


def get_by_system_id(system_id: str) -> Optional[Employee]:
    """Get a Worker by their SystemId."""
    for emp in employee_db:
        if emp["SystemId"] == system_id:
            return Employee(**emp)
    return None


__all__ = ["Employee", "get_by_system_id"]
