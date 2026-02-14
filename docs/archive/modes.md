

# Terms
object - one line item/resource that a set of users are associated with
notification - one instance of an event to be sent to a user about an object
cycle - a full set of the notification escalations.  A cycle must define some notification schedule and number of esclations (or max elapse time for cycle)
campaign - Represents a sequence of cycles.  The objects in a campaign are defined in the datasource view, which must contain a set of required fields.  A campain must define some cycle schedule with no implicit end - cycles will continue indefinetely as long as the campaing is enabled.  Campaign frequency should be longer than the length of a cycle (where to enforce this?).
(Overlapping cycles is maybe technically possible but need to think what would happen)




# SVT - Start email campaign at regular intervals which must be longer than the escalation cycle
1 view with list of object id and list of system ids

# AVT - review at regular interval (this might be a subset of SVT)
1 view with list of object id and ordered list of system ids per month

# TODO - I think CVT mode will need to add the true concept of "mode" becuase it will act differenetly.
# CVT - watching for missing cotacts
Provide view with list of object id and list of system ids


# Datasource View requirements
Each of the modes require a view with the same fields.  This can be made very fleixble, a view on either side should work.  Or even an API or HTTP endpoint with inventory.  We should be able to connect and parse anything but we need to have some known metadata no matter what it's named.
- object_identifier
- system_id_1
- system_id_2
- system_id_3
- system_id_x
- last_updated_date and/or last_verified_date, maybe depending on how their interface oe workflow works, maybe add support for other flags?
- any other metadata or maybe a url for the user to follow?

TODO: think about how to store or expect to receive that ordered list of system ids, it would be nice to support any number.  Maybe the interface should say the ECHO will "SELECT * FROM view_" and expect to find

# Detecting updates
uses:
- last_updated_date
- last_verified_date
- maybe diffs contacts to see if updated?
- maybe a hash on other metadata to indicate to stop the notifications for this cycle
- etc


All objects of same type will escalate together