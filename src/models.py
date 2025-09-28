"module"

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class Employee(BaseModel):
    """
    Worker object representing an employee.

    Contains employee identifiers and contact information for tracking
    and notification purposes.
    """

    GlobalId: int = Field(..., description="Global identifier for the worker")
    SystemId: str = Field(..., description="System-specific identifier for the worker")
    FirstName: str = Field(..., description="Worker's first name")
    LastName: str = Field(..., description="Worker's last name")
    InternetEmailAddress: str = Field(..., description="Worker's email address")
    SupervisorSystemId: Optional[str] = Field(
        None, description="System ID of the worker's supervisor"
    )
    JobTitle: str = Field(..., description="Worker's job title")


class Resource(BaseModel):
    """
    Campaign Object representing a data object that can be tracked and verified.

    This object contains identifiers for contacts across multiple systems,
    tracking URLs, and timestamp information for verification and updates.
    """

    object_id: str = Field(..., description="Unique identifier for the object.")

    contact_id_1: Optional[str] = Field(
        None,
        description="Contact / employee identifier for the person associated with the object in system 1.",
    )
    contact_id_2: Optional[str] = Field(
        None,
        description="Contact / employee identifier for the person associated with the object in system 2.",
    )
    contact_id_3: Optional[str] = Field(
        None,
        description="Contact / employee identifier for the person associated with the object in system 3.",
    )
    contact_id_4: Optional[str] = Field(
        None,
        description="Contact / employee identifier for the person associated with the object in system 4.",
    )

    edit_url: Optional[HttpUrl] = Field(
        None, description="HTTP URL where the object can be viewed or edited."
    )

    last_verified_date: datetime = Field(
        ..., description="The last date the object was verified."
    )
    last_updated_date: Optional[datetime] = Field(
        None, description="The last date the object was updated."
    )


class Reviewable(Resource):
    """
    Campaign Object with ECHO metadata for notification tracking.

    Extends the base CampaignObject with additional fields for tracking
    notification status, escalation levels, and campaign cycles.
    """

    last_notified_date: Optional[datetime] = Field(
        None, description="The last date a notification was sent for this object."
    )
    notification_status: Optional[str] = Field(
        None,
        description="Current status of notifications (e.g., 'in_progress', 'completed', 'paused').",
    )
    current_escalation_level: Optional[int] = Field(
        None, description="Current escalation level for notifications.", ge=0
    )
    max_escalations: Optional[int] = Field(
        None, description="Maximum number of escalation levels allowed.", ge=0
    )
    cycle_start_date: Optional[datetime] = Field(
        None, description="Date when the current notification cycle started."
    )
    cycle_end_date: Optional[datetime] = Field(
        None,
        description="Date when the current notification cycle ended (if completed).",
    )
    campaign_id: Optional[str] = Field(
        None, description="Identifier for the campaign associated with this object."
    )


class Notification(BaseModel):
    """
    Outgoing Notification object for sending notifications to recipients.

    Contains information needed to send a notification about a specific object
    to a designated recipient.
    """

    recipient: str = Field(
        ...,
        description="Contact / employee identifier for the person to receive the notification.",
    )
    object_id: str = Field(
        ...,
        description="Unique identifier for the object associated with the notification.",
    )
    edit_url: HttpUrl = Field(
        ..., description="HTTP URL where the object can be viewed or edited."
    )
    campaign_id: Optional[str] = Field(
        None,
        description="Identifier for the campaign associated with the notification.",
    )


# Example usage and factory functions
def create_sample_campaign_object() -> Resource:
    """Create a sample campaign object for testing purposes."""
    return Resource(
        object_id="obj_123456",
        contact_id_1="v5x1234",
        contact_id_2="v5x5678",
        contact_id_3="v5x9012",
        contact_id_4="v5x3456",
        edit_url="https://app.example.com/objects/obj_123456/edit",
        last_verified_date=datetime(2024, 10, 1, 12, 0, 0),
        last_updated_date=datetime(2024, 10, 15, 12, 0, 0),
    )


def create_sample_campaign_object_with_echo() -> Reviewable:
    """Create a sample campaign object with ECHO metadata for testing purposes."""
    return Reviewable(
        object_id="obj_123456",
        contact_id_1="v5x1234",
        contact_id_2="v5x5678",
        contact_id_3="v5x9012",
        contact_id_4="v5x3456",
        edit_url="https://app.example.com/objects/obj_123456/edit",
        last_verified_date=datetime(2024, 10, 1, 12, 0, 0),
        last_updated_date=datetime(2024, 10, 15, 12, 0, 0),
        last_notified_date=datetime(2024, 10, 20, 12, 0, 0),
        notification_status="in_progress",
        current_escalation_level=2,
        max_escalations=3,
        cycle_start_date=datetime(2024, 10, 18, 12, 0, 0),
        cycle_end_date=None,
        campaign_id="camp_001",
    )


def create_sample_outgoing_notification() -> Notification:
    """Create a sample outgoing notification for testing purposes."""
    return Notification(
        recipient="v5x1234",
        object_id="object_123456",
        edit_url="https://app.example.com/objects/obj_123456/edit",
        campaign_id="camp_001",
    )
