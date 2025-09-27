

# Campaign Object
## schema
```json
{
  "type": "object",
  "properties": {
    "object_id": {
      "type": "string",
      "description": "Unique identifier for the object."
    },
    "contact_id_1": {
      "type": "string",
      "description": "Contact / employee identifier for the person associated with the object in system 1."
    },
    "contact_id_2": {
      "type": "string",
      "description": "Contact / employee identifier for the person associated with the object in system 2."
    },
    "contact_id_3": {
      "type": "string",
      "description": "Contact / employee identifier for the person associated with the object in system 3."
    },
    "contact_id_4": {
      "type": "string",
      "description": "Contact / employee identifier for the person associated with the object in system 4."
    },
    "edit_url": {
      "type": "string",
      "format": "uri",
      "description": "HTTP URL where the object can be viewed or edited."
    },
    "last_verified_date": {
      "type": "string",
      "format": "date-time",
      "description": "The last date the object was verified."
    },
    "last_updated_date": {
      "type": "string",
      "format": "date-time",
      "description": "The last date the object was updated."
    },

  },
  "required": ["object_id", "last_verified_date"]
}

```

## example

```json
{
  "object_id": "obj_123456",
  "contact_id_1": "v5x1234",
  "contact_id_2": "v5x5678",
  "contact_id_3": "v5x9012",
  "contact_id_4": "v5x3456",
  "edit_url": "https://app.example.com/objects/obj_123456/edit",
  "last_verified_date": "2024-10-01T12:00:00Z",
  "last_updated_date": "2024-10-15T12:00:00Z"
```

# Object with ECHO metadata
```json
{
  "object_id": "obj_123456",
  "contact_id_1": "v5x1234",
  "contact_id_2": "v5x5678",
  "contact_id_3": "v5x9012",
  "contact_id_4": "v5x3456",
  "edit_url": "https://app.example.com/objects/obj_123456/edit",
  "last_verified_date": "2024-10-01T12:00:00Z",
  "last_updated_date": "2024-10-15T12:00:00Z",
  "last_notified_date": "2024-10-20T12:00:00Z",
  "notification_status": "in_progress",
  "current_escalation_level": 2,
  "max_escalations": 3,
  "cycle_start_date": "2024-10-18T12:00:00Z",
  "cycle_end_date": null, # or max_escalations,
  "campaign_id": "camp_001"
}



# Outgoing Notification
## Schema
```json
{
  "type": "object",
  "properties": {
    "recipient": {
      "type": "string",
      "description": "Contact / employee identifier for the person to receive the notification."
    },
    "object_id": {
      "type": "string",
      "description": "Unique identifier for the object associated with the notification."
    },
    "edit_url": {
      "type": "string",
      "format": "uri",
      "description": "HTTP URL where the object can be viewed or edited."
    },
    "campaign_id": {
      "type": "string",
      "description": "Identifier for the campaign associated with the notification."
    }
  },
  "required": ["recipient", "object_id", "edit_url"]
}
```

## example object
Note: will likely need more here
```json
{
  "recipient": "v5x1234",
  "object_id": "object_123456",
  "edit_url": "https://app.example.com/objects/obj_123456/edit",
  "campaign_id": "camp_001"
}
```