from flask import Flask, request, jsonify
import mysql.connector
import boto3
import requests
import logging
from datetime import datetime

app = Flask(__name__)

# AWS RDS Configuration
RDS_HOST = "your-rds-endpoint.amazonaws.com"
RDS_USER = "your-rds-username"
RDS_PASSWORD = "your-rds-password"
RDS_DB_NAME = "your-database-name"

# SKY API Configuration
SKY_API_BASE_URL = "https://api.sky.blackbaud.com"
SKY_API_HEADERS = {"Authorization": "Bearer YOUR_API_KEY"}

# Establish RDS Database Connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=RDS_HOST,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DB_NAME
        )
        return connection
    except mysql.connector.Error as e:
        logging.error(f"Error connecting to database: {e}")
        return None

# 1. Access Online Sales Records
@app.route('/sales/records', methods=['GET'])
def get_sales_records():
    sales_order_id = request.args.get('sales_order_id')
    try:
        # Fetch sales data from Altru SKY API
        altru_url = f"{SKY_API_BASE_URL}/alt-slsmg/sales/{sales_order_id}/orders"
        altru_response = requests.get(altru_url, headers=SKY_API_HEADERS)
        if altru_response.status_code != 200:
            return jsonify({"error": "Failed to fetch data from Altru"}), 500
        
        altru_data = altru_response.json()

        # Cross-check with local database
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ParkingPasses WHERE Event_ID IN (SELECT Event_ID FROM Events)")
        local_data = cursor.fetchall()
        db.close()

        return jsonify({"altru_data": altru_data, "local_data": local_data})
    except Exception as e:
        logging.error(f"Error fetching sales records: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# 2. Issue Parking Tickets
@app.route('/parking/tickets', methods=['POST'])
def issue_parking_tickets():
    try:
        data = request.json
        event_id = data['event_id']
        pass_type = data['pass_type']
        quantity = data['quantity']

        db = get_db_connection()
        cursor = db.cursor()

        # Insert tickets into database
        for _ in range(quantity):
            cursor.execute("INSERT INTO ParkingPasses (Event_ID, Issued) VALUES (%s, %s)", (event_id, datetime.now()))
        db.commit()
        db.close()

        return jsonify({"message": f"{quantity} parking tickets issued successfully for event {event_id}."})
    except Exception as e:
        logging.error(f"Error issuing parking tickets: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# 3. Check Inventory
@app.route('/inventory/check', methods=['GET'])
def check_inventory():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM ParkingPasses) AS ParkingPassCount,
                (SELECT COUNT(*) FROM Wristbands) AS WristbandCount
        """)
        inventory = cursor.fetchone()
        db.close()

        return jsonify({"inventory": inventory})
    except Exception as e:
        logging.error(f"Error checking inventory: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# 4. List Event Registrants
@app.route('/events/registrants', methods=['GET'])
def get_event_registrants():
    event_id = request.args.get('event_id')
    try:
        # Fetch registrants from Altru SKY API
        altru_url = f"{SKY_API_BASE_URL}/alt-evtmg/events/{event_id}/registrants"
        altru_response = requests.get(altru_url, headers=SKY_API_HEADERS)
        if altru_response.status_code != 200:
            return jsonify({"error": "Failed to fetch registrants from Altru"}), 500

        altru_data = altru_response.json()

        # Fetch registrants from local database
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Customers WHERE C_id IN (SELECT C_id FROM Events WHERE Event_ID = %s)", (event_id,))
        local_data = cursor.fetchall()
        db.close()

        return jsonify({"altru_data": altru_data, "local_data": local_data})
    except Exception as e:
        logging.error(f"Error fetching event registrants: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# 5. Record Sales Entry
@app.route('/sales/record', methods=['POST'])
def record_sales_entry():
    try:
        data = request.json
        customer_id = data['customer_id']
        event_id = data['event_id']
        amount = data['amount']

        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO Sales (C_id, Event_ID, Amount, SaleDate) VALUES (%s, %s, %s, NOW())", 
                       (customer_id, event_id, amount))
        db.commit()
        db.close()

        return jsonify({"message": "Sales entry recorded successfully."})
    except Exception as e:
        logging.error(f"Error recording sales entry: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# 6. Generate Report
@app.route('/reports/generate', methods=['POST'])
def generate_report():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                Events.Name AS EventName, 
                COUNT(ParkingPasses.PP_id) AS ParkingPassCount,
                COUNT(Wristbands.W_id) AS WristbandCount
            FROM Events
            LEFT JOIN ParkingPasses ON Events.Event_ID = ParkingPasses.Event_ID
            LEFT JOIN Wristbands ON Events.Event_ID = Wristbands.Event_ID
            GROUP BY Events.Event_ID
        """)
        report = cursor.fetchall()
        db.close()

        return jsonify({"report": report})
    except Exception as e:
        logging.error(f"Error generating report: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
