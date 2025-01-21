if __name__ == "__main__":
    client = AltruAPIClient()

    # Authenticate
    if client.authenticate():
        # Test fetching a constituent
        constituent = client.get_constituent("example_altru_id")
        print("Constituent:", constituent)

        # Test fetching events
        events = client.get_events("2025-01-01", "2025-01-31")
        print("Events:", events)

        # Test fetching an employee
        employee = client.get_employee("example_employee_id")
        print("Employee:", employee)
    else:
        print("Authentication failed")
