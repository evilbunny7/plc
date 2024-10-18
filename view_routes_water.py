from flask import Blueprint, render_template, jsonify, request
import pyodbc
import logging
from datetime import datetime, timedelta
import pandas as pd
from flask import send_file
from io import BytesIO

# Create a Blueprint for the routes
view_routes_water = Blueprint('view_routes_water', __name__)

def create_connection():
    try:
        conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};Server=192.168.56.2;Database=PLC_BOT;UID=bunny;PWD=4500;')
        logging.debug("Connection established")
        return conn
    except:
        logging.error("Error establishing connection")
        return None

# Route to render the data view page
@view_routes_water.route('/view_data_water', methods=['GET', 'POST'])
def view_data_water():
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
        selected_water_stage = []

        # Check if the user has selected a date range and filters
        if request.method == 'POST':
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            selected_mills = request.form.getlist('mill_name')
            selected_water_stage = request.form.getlist('water_stage')
            if start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        # Ensure the date range does not exceed 3 months
        max_date_range = timedelta(days=90)
        if end_date - start_date > max_date_range:
            start_date = end_date - max_date_range

        # Build the query with filters
        query = """
            SELECT * FROM dbo.StageMovementSummary
            WHERE Date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if selected_mills:
            query += " AND Mill_Name IN ({})".format(','.join(['?'] * len(selected_mills)))
            params.extend(selected_mills)

        if selected_water_stage:
            query += " AND Water_Stage IN ({})".format(','.join(['?'] * len(selected_water_stage)))
            params.extend(selected_water_stage)

        cursor.execute(query, params)
        data = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        logging.debug(f"Data fetched successfully: {data}")

        # Fetch distinct mill names and product names for the dropdowns
        cursor.execute("SELECT DISTINCT Mill_Name FROM dbo.Mill")
        mills = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT Water_Stage FROM dbo.Water_Stage")
        water_stage = [row[0] for row in cursor.fetchall()]

        return render_template('view_data_water.html', data=data, columns=column_names, start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'), mills=mills, water_stage=water_stage, selected_mills=selected_mills, selected_water_stage=selected_water_stage)
    except Exception as e:
        logging.error(f"Error fetching data: {str(e)}")
        return jsonify({'error': 'Failed to fetch data'}), 500
    finally:
        if conn:
            conn.close()
            logging.debug("Connection closed")

@view_routes_water.route('/export_data_water', methods=['GET'])
def export_data_water():
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
        selected_water_stage = request.args.getlist('water_stage')
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
            SELECT Date, Mill_Name, Stage_Name, Opening_Balance, Closing_Balance, Movement
            FROM dbo.StageMovementSummary
            WHERE Date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if selected_mills:
            placeholders = ','.join('?' for _ in selected_mills)
            query += f" AND Mill_Name IN ({placeholders})"
            params.extend(selected_mills)

        if selected_water_stage:
            placeholders = ','.join('?' for _ in selected_water_stage)
            query += f" AND Stage_Name IN ({placeholders})"
            params.extend(selected_water_stage)

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

    
    