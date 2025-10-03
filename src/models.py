"module"

from dataclasses import dataclass


@dataclass
class Campaign:
    "class"

    id: int | None
    name: str
    description: str | None

    def change_description(self, new_description: str | None) -> None:
        "method"
        self.description = new_description


@dataclass
class Employee:
    "class"

    first_name: str
    last_name: str
    global_id: int
    system_id: str
    internet_email_address: str
    job_title: str
    supervisor_system_id: str | None
