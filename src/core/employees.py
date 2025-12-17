"module"

from typing import Optional

from core.models import Employee
from db import db_json

employee_db = db_json.get_db("data/Employees.json")


def get_by_system_id(system_id: str) -> Optional[Employee]:
    """Get a Worker by their SystemId."""
    for emp in employee_db:
        if emp["SystemId"] == system_id:
            return Employee(
                first_name=emp["FirstName"],
                last_name=emp["LastName"],
                global_id=emp["GlobalId"],
                system_id=emp["SystemId"],
                internet_email_address=emp["InternetEmailAddress"],
                job_title=emp["JobTitle"],
                supervisor_system_id=emp["SupervisorSystemId"],
            )
    return None


__all__ = ["Employee", "get_by_system_id"]
