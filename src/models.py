"module"

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class Campaign(BaseModel):
    """
    Campaign config for a notification campaign.

    Contains campaign identifiers, data source information, templates for
    notifications, and scheduling rules.
    """

    campaign_id: int = Field(..., description="Unique identifier for the campaign")
    name: str = Field(..., description="Name of the campaign")
    description: Optional[str] = Field(
        None, description="Optional description of the campaign"
    )


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
