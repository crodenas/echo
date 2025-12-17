"module"

import json
from typing import List, Optional

from core.models import Employee

DB_FILE = "examples/data/Employees.json"
EMPLOYEES: List[Employee] = []

with open(DB_FILE, "r", encoding="utf-8") as fh:
    employee_db = json.load(fh)
    EMPLOYEES = [
        Employee(
            first_name=emp["FirstName"],
            last_name=emp["LastName"],
            global_id=emp["GlobalId"],
            system_id=emp["SystemId"],
            internet_email_address=emp["InternetEmailAddress"],
            job_title=emp["JobTitle"],
            supervisor_system_id=emp.get("SupervisorSystemId"),
        )
        for emp in employee_db
    ]


def get_by_system_id(system_id: str) -> Optional[Employee]:
    """Get a Worker by their SystemId."""
    for emp in EMPLOYEES:
        if emp.system_id == system_id:
            return emp
    return None


__all__ = ["Employee", "get_by_system_id"]
