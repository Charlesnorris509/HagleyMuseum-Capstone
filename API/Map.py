from sqlalchemy.orm import sessionmaker
from models import Customer  # Assuming you have defined your ORM models
from models import Event  # Assuming you have defined your ORM models

Session = sessionmaker(bind=engine)
session = Session()

def insert_customers(customers_data):
    for data in customers_data:
        customer = Customer(
            Member_id=data.get('id'),
            Fname=data.get('first_name'),
            Lname=data.get('last_name'),
            Phone=data.get('phone'),
            Email=data.get('email'),
            Address1=data.get('address_lines'),
            City=data.get('city'),
            State=data.get('state'),
            Zip=data.get('postal_code'),
            Altru_id=data.get('lookup_id')
        )
        session.add(customer)
    session.commit()

def insert_events(events_data):
    for data in events_data:
        event = Event(
            Name=data.get('name'),
            EventDate=data.get('start_date')
        )
        session.add(event)
    session.commit()
