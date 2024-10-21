from flask import Blueprint, render_template, jsonify, request
import pyodbc
import logging
from validators import validate_all_input_values

# Create a Blueprint for the routes
routes = Blueprint('routes', __name__)

# Function to create a new database connection
def create_connection():
    connection_string = 'Driver={ODBC Driver 17 for SQL Server};Server=192.168.56.2;Database=PLC_BOT;UID=bunny;PWD=4500;'
    return pyodbc.connect(connection_string)

# Function to generate a new log_id
def generate_log_id(cursor, actual_date):
    cursor.execute("SELECT MAX(Log_ID) FROM dbo.Mill_Log WHERE Date = ?", actual_date)
    result = cursor.fetchone()
    return result[0] + 1 if result[0] else 1

# Function to get the previous End_Value
def get_previous_end_value(cursor, table, mill_id, id_field, id_value):
    query = f"""
        SELECT TOP 1 End_Value
        FROM {table}
        WHERE Mill_ID = ? AND {id_field} = ?
        ORDER BY Log_ID DESC
    """
    cursor.execute(query, (mill_id, id_value))
    result = cursor.fetchone()
    return result[0] if result else 0

# Route to render the main HTML page
@routes.route('/')
def index():
    return render_template('index.html')

# API route to get data for the first dropdown
@routes.route('/api/get_dropdown_1')
def get_dropdown_1():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Mill_ID, Mill_Name FROM dbo.Mill")
        dropdown_1_data = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        logging.debug(f"Dropdown 1 Data: {dropdown_1_data}")
        return jsonify(dropdown_1_data)
    except Exception as e:
        logging.error(f"Error fetching dropdown 1 data: {str(e)}")
        return jsonify({'error': 'Failed to fetch dropdown 1 data'}), 500
    finally:
        conn.close()

# API route to get data for the second dropdown
@routes.route('/api/get_dropdown_2')
def get_dropdown_2():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Shift_ID, Shift_Type FROM dbo.Shift_Type")
        dropdown_2_data = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        logging.debug(f"Dropdown 2 Data: {dropdown_2_data}")
        return jsonify(dropdown_2_data)
    except Exception as e:
        logging.error(f"Error fetching dropdown 2 data: {str(e)}")
        return jsonify({'error': 'Failed to fetch dropdown 2 data'}), 500
    finally:
        conn.close()

# API route to get data for the third dropdown
@routes.route('/api/get_dropdown_3')
def get_dropdown_3():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Miller_ID, Miller_Name FROM dbo.Miller")
        dropdown_3_data = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        logging.debug(f"Dropdown 3 Data: {dropdown_3_data}")
        return jsonify(dropdown_3_data)
    except Exception as e:
        logging.error(f"Error fetching dropdown 3 data: {str(e)}")
        return jsonify({'error': 'Failed to fetch dropdown 3 data'}), 500
    finally:
        conn.close()

# API route to get product data for dynamic input fields
@routes.route('/api/get_product_data')
def get_product_data():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Product_ID, Product_Name FROM dbo.Product_Table")
        product_data = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        logging.debug(f"Product Data: {product_data}")
        return jsonify(product_data)
    except Exception as e:
        logging.error(f"Error fetching product data: {str(e)}")
        return jsonify({'error': 'Failed to fetch product data'}), 500
    finally:
        conn.close()

# API route to get transfer data for dynamic input fields
@routes.route('/api/get_transfer_data')
def get_transfer_data():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Transfer_ID, Transfer_Type FROM dbo.Transfer_Type")
        transfer_data = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        logging.debug(f"Transfer Data: {transfer_data}")
        return jsonify(transfer_data)
    except Exception as e:
        logging.error(f"Error fetching transfer data: {str(e)}")
        return jsonify({'error': 'Failed to fetch transfer data'}), 500
    finally:
        conn.close()

# API route to get water stage data for dynamic input fields
@routes.route('/api/get_water_stage_data')
def get_water_stage_data():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Stage_ID, Water_Stage FROM dbo.Water_Stage")
        water_stage_data = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        logging.debug(f"Water Stage Data: {water_stage_data}")
        return jsonify(water_stage_data)
    except Exception as e:
        logging.error(f"Error fetching water stage data: {str(e)}")
        return jsonify({'error': 'Failed to fetch water stage data'}), 500
    finally:
        conn.close()

# API route to handle form submission
@routes.route('/api/submit', methods=['POST'])
def submit():
    try:
        conn = create_connection()
        conn.autocommit = False
        cursor = conn.cursor()

        # Get the JSON data from the request
        data = request.get_json()
        logging.debug(f"Received data: {data}")
        if data is None:
            logging.error("No data received in the request.")
            return jsonify({'error': 'No data received'}), 400

        # Extract individual values from the JSON data
        dropdown_1 = data.get('dropdown_1')
        dropdown_2 = data.get('dropdown_2')
        dropdown_3 = data.get('dropdown_3')
        user_date = data.get('User_Date')
        mill_id = dropdown_1  # Use dropdown_1 as mill_id
        input_values_1 = data.get('input_values_1', {})
        input_values_2 = data.get('input_values_2', {})
        input_values_3 = data.get('input_values_3', {})

        # Log the extracted values
        logging.debug(f"dropdown_1: {dropdown_1}, dropdown_2: {dropdown_2}, dropdown_3: {dropdown_3}, user_date: {user_date}, mill_id: {mill_id}")
        logging.debug(f"input_values_1: {input_values_1}")
        logging.debug(f"input_values_2: {input_values_2}")
        logging.debug(f"input_values_3: {input_values_3}")

        # Validate required fields
        if dropdown_1 is None or dropdown_2 is None or dropdown_3 is None or user_date is None or mill_id is None:
            logging.error("Missing required fields in the request data.")
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate all input values
        is_valid, error_message = validate_all_input_values(data)
        if not is_valid:
            return jsonify({'error': 'Opening balance cannot be less than closing balance please review your input or call an admin'}), 400

        # Insert into Mill_Log and retrieve the Log_ID
        cursor.execute("""
            INSERT INTO dbo.Mill_Log (Date, Shift_ID, Miller_ID, Mill_ID, Actual_Date)
            OUTPUT INSERTED.Log_ID
            VALUES (?, ?, ?, ?, ?);
        """, (user_date, dropdown_2, dropdown_3, mill_id, user_date))
        
        # Retrieve the auto-generated Log_ID
        log_id = cursor.fetchone()[0]
        logging.debug(f"Generated log_id: {log_id}")

        # Use the retrieved log_id for subsequent inserts
        # Insert into Product_Movement_Log
        for product_id, end_value in input_values_1.items():
            if end_value is None:
                continue
            previous_value = get_previous_end_value(cursor, 'dbo.Product_Movement_Log', mill_id, 'Product_ID', product_id)
            movement = end_value - previous_value
            cursor.execute("""
                INSERT INTO dbo.Product_Movement_Log (Log_ID, Product_ID, End_Value, Scale_Opening_Value, Movement, Shift, Miller, Date, Mill_ID)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (log_id, product_id, end_value, previous_value, movement, dropdown_2, dropdown_3, user_date, mill_id))

        # Insert into Transfer_Movement_Log
        for transfer_id, end_value in input_values_2.items():
            if end_value is None:
                continue
            previous_value = get_previous_end_value(cursor, 'dbo.Transfer_Movement_Log', mill_id, 'Transfer_ID', transfer_id)
            movement = end_value - previous_value
            cursor.execute("""
                INSERT INTO dbo.Transfer_Movement_Log (Log_ID, Transfer_ID, End_Value, Scale_Opening_Value, Movement, Shift, Miller, Date, Mill_ID)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (log_id, transfer_id, end_value, previous_value, movement, dropdown_2, dropdown_3, user_date, mill_id))

        # Insert into Stage_Movement_Log
        for stage_id, end_value in input_values_3.items():
            if end_value is None:
                continue
            previous_value = get_previous_end_value(cursor, 'dbo.Stage_Movement_Log', mill_id, 'Stage_ID', stage_id)
            movement = end_value - previous_value
            cursor.execute("""
                INSERT INTO dbo.Stage_Movement_Log (Log_ID, Stage_ID, End_Value, Scale_Opening_Value, Movement, Shift, Miller, Date, Mill_ID)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (log_id, stage_id, end_value, previous_value, movement, dropdown_2, dropdown_3, user_date, mill_id))

        # Commit the transaction to save the changes in the database
        conn.commit()

        logging.debug("Data submitted successfully")
        return jsonify({'status': 'success'})

    except Exception as e:
        logging.error(f"Error submitting data: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to submit data'}), 500

    finally:
        conn.close()
