"module"

from dataclasses import dataclass


@dataclass
class Campaign:
    "class"

    id: int | None
    name: str
    description: str

    def change_description(self, new_description: str):
        "method"
        self.description = new_description
