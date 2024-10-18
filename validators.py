import pyodbc
import logging

# Function to create a new database connection
def create_connection():
    connection_string = 'Driver={ODBC Driver 17 for SQL Server};Server=192.168.56.2;Database=PLC_BOT;UID=bunny;PWD=4500;'
    return pyodbc.connect(connection_string)

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

def validate_input_values(input_values, previous_values):
    """
    Validate that the input values are not smaller than the opening scale values.

    :param input_values: Dictionary of input values (end values).
    :param previous_values: Dictionary of previous values (opening scale values).
    :return: Tuple (is_valid, error_message)
    """
    for key, end_value in input_values.items():
        if end_value is None or end_value == '':
            continue  # Skip validation if no input value is provided
        opening_value = previous_values.get(key, 0)
        if end_value < opening_value:
            return False, f"End value for ID {key} ({end_value}) is smaller than the opening scale value ({opening_value})."
    return True, ""

def validate_all_input_values(data):
    try:
        conn = create_connection()
        cursor = conn.cursor()

        dropdown_1 = data.get('dropdown_1')
        mill_id = int(dropdown_1)  # Ensure mill_id is an integer
        input_values_1 = {int(k): int(v) if v else None for k, v in data.get('input_values_1', {}).items()}
        input_values_2 = {int(k): int(v) if v else None for k, v in data.get('input_values_2', {}).items()}
        input_values_3 = {int(k): int(v) if v else None for k, v in data.get('input_values_3', {}).items()}

        # Validate input values for Product_Movement_Log
        previous_values_1 = {product_id: get_previous_end_value(cursor, 'dbo.Product_Movement_Log', mill_id, 'Product_ID', product_id) for product_id in input_values_1.keys()}
        is_valid, error_message = validate_input_values(input_values_1, previous_values_1)
        if not is_valid:
            return False, error_message

        # Validate input values for Transfer_Movement_Log
        previous_values_2 = {transfer_id: get_previous_end_value(cursor, 'dbo.Transfer_Movement_Log', mill_id, 'Transfer_ID', transfer_id) for transfer_id in input_values_2.keys()}
        is_valid, error_message = validate_input_values(input_values_2, previous_values_2)
        if not is_valid:
            return False, error_message

        # Validate input values for Stage_Movement_Log
        previous_values_3 = {stage_id: get_previous_end_value(cursor, 'dbo.Stage_Movement_Log', mill_id, 'Stage_ID', stage_id) for stage_id in input_values_3.keys()}
        is_valid, error_message = validate_input_values(input_values_3, previous_values_3)
        if not is_valid:
            return False, error_message

        return True, ""

    except Exception as e:
        logging.error(f"Error validating input values: {str(e)}")
        return False, "Failed to validate input values"

    finally:
        conn.close()