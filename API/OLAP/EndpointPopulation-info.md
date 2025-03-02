# Data Classes and Attributes from DB_Fireworks.sql

## Customers
- **Attributes**: `C_id`, `Member_id`, `MembershipLevel`, `Fname`, `Lname`, `Phone`, `Email`, `Address1`, `Address2`, `City`, `Zip`, `State`, `Attended`, `Paid`, `Cancelled`
- **Populated by**:
  - `/registrants` (GET) - Retrieves event registrants, which can be mapped to customers.
  - `/events/{event_id}/registrants` (GET) - Retrieves registrants for a specific event.
  - `/registrants/search` (GET) - Searches for event registrants.

## Employees
- **Attributes**: `E_id`, `Fname`, `Lname`, `Phone`, `Email`
- **Populated by**:
  - No direct endpoint for employees. Employees might be inferred from other data (e.g., event coordinators).

## Events
- **Attributes**: `Event_ID`, `C_id`, `E_id`, `Name`, `EventDate`
- **Populated by**:
  - `/events` (GET) - Retrieves a list of events.
  - `/events/{event_id}` (GET) - Retrieves a specific event.
  - `/events/search` (GET) - Searches for events.

## Wristbands
- **Attributes**: `W_id`, `Event_ID`, `Issued`
- **Populated by**:
  - 

## ParkingPasses
- **Attributes**: `PP_id`, `Event_ID`, `Issued`
- **Populated by**:
  - /occurrences

## PassTypes
- **Attributes**: `PT_id`, `PP_id`, `PassTypes`, `Cost`
- **Populated by**:
  - /jobs

## Departments
- **Attributes**: `D_id`, `E_id`, `DName`
- **Populated by**:
  - /jobs
