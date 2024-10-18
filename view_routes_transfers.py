from flask import Blueprint, render_template, jsonify, request
import pyodbc
import logging
from datetime import datetime, timedelta
import pandas as pd
from flask import send_file
from io import BytesIO

# Create a Blueprint for the routes
view_routes_transfers = Blueprint('view_routes_transfers', __name__)

def create_connection():
    try:
        conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};Server=192.168.56.2;Database=PLC_BOT;UID=bunny;PWD=4500;')
        logging.debug("Connection established")
        return conn
    except:
        logging.error("Error establishing connection")
        return None

# Route to render the data view page
@view_routes_transfers.route('/view_data_transfers', methods=['GET', 'POST'])
def view_data_transfers():
    conn = None
    try:
        conn = create_connection()
        if conn is None:
            raise Exception("Failed to establish connection")
        
        cursor = conn.cursor()
        logging.debug("Fetching data")

        # Get the current date and calculate the date 14 days ago
        end_date = datetime.now()
        start_date = end_date - timedelta(days=14)

        # Initialize filters
        selected_mills = []
        selected_transfers = []

        # Check if the user has selected a date range and filters
        if request.method == 'POST':
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            selected_mills = request.form.getlist('mill_name')
            selected_transfers = request.form.getlist('transfer_type')
            if start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        # Ensure the date range does not exceed 3 months
        max_date_range = timedelta(days=90)
        if end_date - start_date > max_date_range:
            start_date = end_date - max_date_range

        # Build the query with filters
        query = """
            SELECT * FROM dbo.TransferMovementSummary
            WHERE Date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if selected_mills:
            query += " AND Mill_Name IN ({})".format(','.join(['?'] * len(selected_mills)))
            params.extend(selected_mills)

        if selected_transfers:
            query += " AND Transfer_Type IN ({})".format(','.join(['?'] * len(selected_transfers)))
            params.extend(selected_transfers)

        cursor.execute(query, params)
        data = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        logging.debug(f"Data fetched successfully: {data}")

        # Fetch distinct mill names and product names for the dropdowns
        cursor.execute("SELECT DISTINCT Mill_Name FROM dbo.Mill")
        mills = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT Transfer_Type FROM dbo.Transfer_Type")
        transfers = [row[0] for row in cursor.fetchall()]

        return render_template('view_data_transfers.html', data=data, columns=column_names, start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'), mills=mills, transfers=transfers, selected_mills=selected_mills, selected_transfers=selected_transfers)
    except Exception as e:
        logging.error(f"Error fetching data: {str(e)}")
        return jsonify({'error': 'Failed to fetch data'}), 500
    finally:
        if conn:
            conn.close()
            logging.debug("Connection closed")

@view_routes_transfers.route('/export_data_transfers', methods=['GET'])
def export_data_transfers():
    conn = None
    try:
        conn = create_connection()
        if conn is None:
            raise Exception("Failed to establish connection")
        
        cursor = conn.cursor()
        logging.debug("Fetching data for export")

        # Get the current date and calculate the date 14 days ago
        end_date = datetime.now()
        start_date = end_date - timedelta(days=14)

        # Initialize filters
        selected_mills = request.args.getlist('mill_name')
        selected_transfers = request.args.getlist('transfer_type')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        # Ensure the date range does not exceed 3 months
        max_date_range = timedelta(days=90)
        if end_date - start_date > max_date_range:
            start_date = end_date - max_date_range

        # Fetch data based on filters
        query = """
            SELECT Date, Mill_Name, Transfer_Type, Opening_Balance, Closing_Balance, Movement
            FROM dbo.TransferMovementSummary
            WHERE Date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if selected_mills:
            placeholders = ','.join('?' for _ in selected_mills)
            query += f" AND Mill_Name IN ({placeholders})"
            params.extend(selected_mills)

        if selected_transfers:
            placeholders = ','.join('?' for _ in selected_transfers)
            query += f" AND Transfer_Type IN ({placeholders})"
            params.extend(selected_transfers)

        cursor.execute(query, params)
        data = cursor.fetchall()
        
        # Log the fetched data and cursor description
        logging.debug(f"Fetched data: {data}")
        logging.debug(f"Cursor description: {cursor.description}")
        
        # Ensure columns are correctly derived from cursor description
        columns = [desc[0] for desc in cursor.description]
        logging.debug(f"Columns: {columns}")

        # Check the shape of the data
        logging.debug(f"Data shape: {len(data)} rows, {len(data[0]) if data else 0} columns")

        # Convert the data to a pandas DataFrame
        if data:
            df = pd.DataFrame.from_records(data, columns=columns)
            logging.debug(f"DataFrame created with shape: {df.shape}")
        else:
            df = pd.DataFrame(columns=columns)
            logging.debug("No data fetched, creating empty DataFrame")
        
        # Create a BytesIO buffer to hold the Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        output.seek(0)
        
        # Send the file to the user
        # Note: 'attachment_filename' is deprecated in Flask 2.0+, use 'download_name' instead
        return send_file(output, download_name='exported_data.xlsx', as_attachment=True)
    except Exception as e:
        logging.error(f"Error exporting data: {str(e)}")
        return jsonify({'error': 'Failed to export data'}), 500
    finally:
        if conn:
            conn.close()
            logging.debug("Connection closed")
