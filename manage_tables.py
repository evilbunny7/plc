from flask import Blueprint, render_template, request, jsonify
import pyodbc
import logging

# Create a Blueprint for the manage tables routes
manage_tables_bp = Blueprint('manage_tables_bp', __name__)

# Function to create a new database connection
def create_connection():
    connection_string = 'Driver={ODBC Driver 17 for SQL Server};Server=192.168.56.2;Database=PLC_BOT;UID=bunny;PWD=4500;'
    return pyodbc.connect(connection_string)

# Table configuration
table_config = {
    'Mill': ('Mill_ID', 'Mill_Name'),
    'Miller': ('Miller_ID', 'Miller_Name'),
    'Transfer_Type': ('Transfer_ID', 'Transfer_Type'),
    'Water_Conditioning': ('Conditioning_ID', 'Conditioning_Type'),
    'Water_Stage': ('Stage_ID', 'Water_Stage'),
    'Product_Table': ('Product_ID', 'Product_Name')
}

# Generic function to get all records from a table
def get_all_records(table_name, id_column, name_column):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT {id_column}, {name_column} FROM dbo.{table_name}")
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

@manage_tables_bp.route('/manage_tables')
def manage_tables():
    return render_template('manage_tables.html')