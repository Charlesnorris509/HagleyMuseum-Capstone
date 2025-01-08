from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', hours=24)
def scheduled_sync():
    access_token = get_access_token()
    customers_data = fetch_constituents(access_token)
    insert_customers(customers_data)
    events_data = fetch_events(access_token)
    insert_events(events_data)

scheduler.start()
