# dash_module.py
import plotly.graph_objects as go
import plotly.io as pio
from flask import Blueprint, render_template, request
import pyodbc

# Create a Blueprint for the Dash module
dash_bp = Blueprint('dash_bp', __name__)

# Create a function to connect to the database
def connect_to_db():
    # Connect to the database
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=192.168.56.2;DATABASE=PLC_BOT;UID=bunny;PWD=4500')
    cursor = conn.cursor()
    return conn, cursor

# Function to get the end values for each product within a specific mill
def get_end_values(mill_id):
    conn, cursor = connect_to_db()
    query = """
    SELECT p.Product_ID, p.Product_Name, m.Mill_Name, SUM(l.Movement) AS Total_End_Value
    FROM dbo.Product_Movement_Log l
    JOIN dbo.Product_Table p ON l.Product_ID = p.Product_ID
    JOIN dbo.Mill m ON l.Mill_ID = m.Mill_ID
    WHERE l.Mill_ID = ?
    GROUP BY p.Product_ID, p.Product_Name, m.Mill_Name
    """
    cursor.execute(query, mill_id)
    results = cursor.fetchall()
    conn.close()
    return [{'Product_ID': row.Product_ID, 'Product_Name': row.Product_Name, 'Mill_Name': row.Mill_Name, 'Total_End_Value': row.Total_End_Value} for row in results]

# Function to get the transfer values for each transfer type within a specific mill
def get_transfer_values(mill_id):
    conn, cursor = connect_to_db()
    query = """
    SELECT t.Transfer_ID, t.Transfer_Type, m.Mill_Name, SUM(l.Movement) AS Total_End_Value
    FROM dbo.Transfer_Movement_Log l
    JOIN dbo.Transfer_Type t ON l.Transfer_ID = t.Transfer_ID
    JOIN dbo.Mill m ON l.Mill_ID = m.Mill_ID
    WHERE l.Mill_ID = ?
    GROUP BY t.Transfer_ID, t.Transfer_Type, m.Mill_Name
    """
    cursor.execute(query, mill_id)
    results = cursor.fetchall()
    conn.close()
    return [{'Transfer_ID': row.Transfer_ID, 'Transfer_Type': row.Transfer_Type, 'Mill_Name': row.Mill_Name, 'Total_End_Value': row.Total_End_Value} for row in results]

@dash_bp.route('/dash')
def render_dash():
    view = request.args.get('view', 'view1')
    figures = {}

    if view == 'view1':
        mills = ['1', '2', '3']
        for mill_id in mills:
            end_values = get_end_values(mill_id)
            figures[mill_id] = []
            for entry in end_values:
                product_id = entry['Product_ID']
                product_name = entry['Product_Name']
                mill_name = entry['Mill_Name']
                end_value_kg = entry['Total_End_Value']
                end_value_tons = end_value_kg / 1000  # Convert to metric tons
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=end_value_tons,
                    title={'text': f"{mill_name} - {product_name} End Value (tons)", 'font': {'family': 'Courier New, monospace', 'size': 18, 'color': '#8A0303'}},
                    gauge={
                        'axis': {'range': [None, 1000], 'tickwidth': 2, 'tickcolor': "#8B4513"},
                        'bar': {'color': "#8B4513"},
                        'bgcolor': "rgba(245, 222, 179, 0.5)",  # More transparent background color
                        'borderwidth': 2,
                        'bordercolor': "#8B4513",
                        'steps': [
                            {'range': [0, 250], 'color': "#D2B48C"},
                            {'range': [250, 500], 'color': "#DEB887"},
                            {'range': [500, 750], 'color': "#F4A460"},
                            {'range': [750, 1000], 'color': "#CD853F"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': end_value_tons
                        }
                    }
                ))
                fig.update_layout(
                    width=360, 
                    height=320,
                    paper_bgcolor="rgba(245, 222, 179, 0.72)",  # More transparent background color
                    font={'color': "#8B4513", 'family': "Courier New, monospace"}
                )
                figures[mill_id].append(pio.to_html(fig, full_html=False))
    elif view == 'view2':
        # Add logic for view2
        pass
    elif view == 'view3':
        mills = ['1', '2', '3']
        for mill_id in mills:
            transfer_values = get_transfer_values(mill_id)
            figures[mill_id] = []
            for entry in transfer_values:
                transfer_id = entry['Transfer_ID']
                transfer_type_name = entry['Transfer_Type']
                mill_name = entry['Mill_Name']
                end_value_kg = entry['Total_End_Value']
                end_value_tons = end_value_kg / 1000  # Convert to metric tons
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=end_value_tons,
                    title={'text': f"{mill_name} - {transfer_type_name} Transfer Value (tons)", 'font': {'family': 'Courier New, monospace', 'size': 18, 'color': '#8A0303'}},
                    gauge={
                        'axis': {'range': [None, 1000], 'tickwidth': 2, 'tickcolor': "#8B4513"},
                        'bar': {'color': "#8B4513"},
                        'bgcolor': "rgba(245, 222, 179, 0.5)",  # More transparent background color
                        'borderwidth': 2,
                        'bordercolor': "#8B4513",
                        'steps': [
                            {'range': [0, 250], 'color': "#D2B48C"},
                            {'range': [250, 500], 'color': "#DEB887"},
                            {'range': [500, 750], 'color': "#F4A460"},
                            {'range': [750, 1000], 'color': "#CD853F"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': end_value_tons
                        }
                    }
                ))
                fig.update_layout(
                    width=360, 
                    height=320,
                    paper_bgcolor="rgba(245, 222, 179, 0.72)",  # More transparent background color
                    font={'color': "#8B4513", 'family': "Courier New, monospace"}
                )
                figures[mill_id].append(pio.to_html(fig, full_html=False))

    return render_template('dash.html', figures=figures)