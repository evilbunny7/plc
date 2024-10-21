from flask import Blueprint, render_template, request, jsonify
import pyodbc
import logging

# Create a Blueprint for the manage tables routes
manage_tables_bp = Blueprint('manage_tables_bp', __name__)

# Function to create a new database connection
def create_connection():
    connection_string = 'Driver={ODBC Driver 17 for SQL Server};Server=192.168.56.2;Database=PLC_BOT;UID=bunny;PWD=4500;'
    return pyodbc.connect(connection_string)

# Updated table configuration
table_config = {
    'Mill': ('Mill_ID', 'Mill_Name'),
    'Miller': ('Miller_ID', 'Miller_Name'),
    'Transfer_Type': ('Transfer_ID', 'Transfer_Type'),
    'Water_Conditioning': ('Conditioning_ID', 'Conditioning_Type'),
    'Water_Stage': ('Stage_ID', 'Water_Stage'),
    'Product_Table': ('Product_ID', 'Product_Name'),
    'Product_Movement_Log': ('Product_ID', 'Product_Name'),
    'Transfer_Movement_Log': ('Transfer_ID', 'Transfer_Type'),
    'Stage_Movement_Log': ('Stage_ID', 'Water_Stage')
}

# Updated get_all_records function
def get_all_records(table_name, id_column, name_column):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        
        if table_name in ['Product_Movement_Log', 'Transfer_Movement_Log', 'Stage_Movement_Log']:
            join_table = {
                'Product_Movement_Log': 'Product_Table',
                'Transfer_Movement_Log': 'Transfer_Type',
                'Stage_Movement_Log': 'Water_Stage'
            }[table_name]
            
            query = f"""
                SELECT DISTINCT l.Log_ID, t.{id_column}, t.{name_column}, l.Mill_ID, m.Mill_Name,
                       ml.Date, s.Shift_Type, mr.Miller_Name, l.Scale_Opening_Value, l.End_Value, l.Movement
                FROM dbo.{table_name} l
                JOIN dbo.{join_table} t ON l.{id_column} = t.{id_column}
                JOIN dbo.Mill m ON l.Mill_ID = m.Mill_ID
                JOIN dbo.Mill_Log ml ON l.Log_ID = ml.Log_ID
                JOIN dbo.Shift_Type s ON ml.Shift_ID = s.Shift_ID
                JOIN dbo.Miller mr ON ml.Miller_ID = mr.Miller_ID
                ORDER BY l.Log_ID DESC, ml.Date DESC
            """
            cursor.execute(query)
            records = [{
                'log_id': row[0],
                'id': row[1],
                'name': row[2],
                'mill_id': row[3],
                'mill_name': row[4],
                'date': row[5].strftime('%Y-%m-%d'),
                'shift': row[6],
                'miller': row[7],
                'opening_balance': row[8],
                'closing_balance': row[9],
                'movement': row[10],
                'id_field': id_column
            } for row in cursor.fetchall()]
        else:
            query = f"SELECT {id_column}, {name_column} FROM dbo.{table_name}"
            cursor.execute(query)
            records = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
        return jsonify(records)
    except Exception as e:
        logging.error(f"Error fetching records from {table_name}: {str(e)}")
        return jsonify({'error': f'Failed to fetch records from {table_name}'}), 500
    finally:
        conn.close()

# Generic function to add a record to a table
def add_record(table_name, name_column):
    try:
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO dbo.{table_name} ({name_column}) VALUES (?)", name)
        conn.commit()
        return jsonify({'message': f'Record added successfully to {table_name}'}), 201
    except Exception as e:
        logging.error(f"Error adding record to {table_name}: {str(e)}")
        return jsonify({'error': f'Failed to add record to {table_name}'}), 500
    finally:
        conn.close()

# Generic function to update a record in a table
def update_record(table_name, id_column, name_column, record_id):
    try:
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE dbo.{table_name} SET {name_column} = ? WHERE {id_column} = ?", (name, record_id))
        conn.commit()
        return jsonify({'message': f'Record updated successfully in {table_name}'})
    except Exception as e:
        logging.error(f"Error updating record in {table_name}: {str(e)}")
        return jsonify({'error': f'Failed to update record in {table_name}'}), 500
    finally:
        conn.close()

# Generic function to delete a record from a table
def delete_record(table_name, id_column, record_id):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM dbo.{table_name} WHERE {id_column} = ?", record_id)
        conn.commit()
        return jsonify({'message': f'Record deleted successfully from {table_name}'})
    except Exception as e:
        logging.error(f"Error deleting record from {table_name}: {str(e)}")
        return jsonify({'error': f'Failed to delete record from {table_name}'}), 500
    finally:
        conn.close()

# Routes for each table
@manage_tables_bp.route('/api/<table_name>', methods=['GET', 'POST'])
def handle_table(table_name):
    if table_name not in table_config:
        return jsonify({'error': 'Invalid table name'}), 400
    
    id_column, name_column = table_config[table_name]
    
    if request.method == 'GET':
        return get_all_records(table_name, id_column, name_column)
    elif request.method == 'POST':
        return add_record(table_name, name_column)

@manage_tables_bp.route('/api/<table_name>/<int:record_id>', methods=['PUT', 'DELETE'])
def handle_record(table_name, record_id):
    if table_name not in table_config:
        return jsonify({'error': 'Invalid table name'}), 400
    
    id_column, name_column = table_config[table_name]
    
    if request.method == 'PUT':
        return update_record(table_name, id_column, name_column, record_id)
    elif request.method == 'DELETE':
        return delete_record(table_name, id_column, record_id)

# Updated correct_entry function
@manage_tables_bp.route('/api/correct', methods=['POST'])
def correct_entry():
    try:
        conn = create_connection()
        conn.autocommit = False
        cursor = conn.cursor()

        data = request.get_json()
        log_id = data.get('log_id')
        table_name = data.get('table_name')
        id_field = data.get('id_field')
        id_value = data.get('id_value')
        new_end_value = data.get('new_end_value')
        mill_id = data.get('mill_id')

        # Validate the new end value
        is_valid, error_message = validate_new_end_value(cursor, table_name, id_field, id_value, mill_id, log_id, new_end_value)
        if not is_valid:
            return jsonify({'status': 'error', 'message': error_message}), 400

        # Update the End_Value in the specified table
        cursor.execute(f"""
            UPDATE dbo.{table_name}
            SET End_Value = ?
            WHERE Log_ID = ? AND {id_field} = ? AND Mill_ID = ?
        """, (new_end_value, log_id, id_value, mill_id))

        # Recalculate movements for the corrected entry and all subsequent entries
        recalculate_movements(cursor, table_name, log_id, id_field, id_value, mill_id)

        conn.commit()
        return jsonify({'status': 'success', 'message': 'Correction applied successfully'})

    except Exception as e:
        logging.error(f"Error applying correction: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({'error': 'Failed to apply correction'}), 500

    finally:
        conn.close()

def validate_new_end_value(cursor, table_name, id_field, id_value, mill_id, log_id, new_end_value):
    # Check if the new end value is less than any future opening balance
    cursor.execute(f"""
        SELECT TOP 1 Scale_Opening_Value
        FROM dbo.{table_name}
        WHERE {id_field} = ? AND Mill_ID = ? AND Log_ID > ?
        ORDER BY Log_ID ASC
    """, (id_value, mill_id, log_id))
    next_opening_balance = cursor.fetchone()

    if next_opening_balance and new_end_value < next_opening_balance[0]:
        return False, f"New end value ({new_end_value}) cannot be less than the next opening balance ({next_opening_balance[0]})"

    # Check if the new end value is greater than the previous closing balance
    cursor.execute(f"""
        SELECT TOP 1 End_Value
        FROM dbo.{table_name}
        WHERE {id_field} = ? AND Mill_ID = ? AND Log_ID < ?
        ORDER BY Log_ID DESC
    """, (id_value, mill_id, log_id))
    prev_closing_balance = cursor.fetchone()

    if prev_closing_balance and new_end_value < prev_closing_balance[0]:
        return False, f"New end value ({new_end_value}) cannot be less than the previous closing balance ({prev_closing_balance[0]})"

    return True, ""

def recalculate_movements(cursor, table_name, start_log_id, id_field, id_value, mill_id):
    # Fetch all entries for the specific product/transfer/stage, including and after the corrected entry
    cursor.execute(f"""
        SELECT Log_ID, End_Value, Scale_Opening_Value, Movement
        FROM dbo.{table_name}
        WHERE {id_field} = ? AND Mill_ID = ? AND Log_ID >= ?
        ORDER BY Log_ID
    """, (id_value, mill_id, start_log_id))
    entries = cursor.fetchall()

    for i in range(len(entries)):
        curr_entry = entries[i]
        
        if i == 0:
            # For the first (corrected) entry, we need to fetch the previous entry to calculate the new movement
            cursor.execute(f"""
                SELECT TOP 1 End_Value
                FROM dbo.{table_name}
                WHERE {id_field} = ? AND Mill_ID = ? AND Log_ID < ?
                ORDER BY Log_ID DESC
            """, (id_value, mill_id, curr_entry.Log_ID))
            prev_end_value = cursor.fetchone()
            prev_end_value = prev_end_value[0] if prev_end_value else 0
        else:
            prev_end_value = entries[i-1].End_Value

        new_movement = curr_entry.End_Value - prev_end_value
        
        cursor.execute(f"""
            UPDATE dbo.{table_name}
            SET Movement = ?, Scale_Opening_Value = ?
            WHERE Log_ID = ? AND {id_field} = ? AND Mill_ID = ?
        """, (new_movement, prev_end_value, curr_entry.Log_ID, id_value, mill_id))

@manage_tables_bp.route('/manage_tables')
def manage_tables():
    return render_template('manage_tables.html')
