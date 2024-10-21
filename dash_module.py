# dash_module.py
import plotly.graph_objects as go
import plotly.io as pio
from flask import Blueprint, render_template, request, jsonify
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
    try:
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
        print(f"Raw results for mill_id {mill_id}:", results)  # Add this line
        return [{'Transfer_ID': row.Transfer_ID, 'Transfer_Type': row.Transfer_Type, 'Mill_Name': row.Mill_Name, 'Total_End_Value': row.Total_End_Value} for row in results]
    except Exception as e:
        print(f"Error in get_transfer_values: {str(e)}")  # Change logging to print
        return []
    finally:
        conn.close()

def get_stage_values(mill_id):
    conn, cursor = connect_to_db()
    try:
        query = """
        SELECT s.Stage_ID, s.Water_Stage, m.Mill_Name, SUM(l.Movement) AS Total_Stage_Value
        FROM dbo.Stage_Movement_Log l
        JOIN dbo.Water_Stage s ON l.Movement_ID = s.Stage_ID
        JOIN dbo.Mill m ON l.Mill_ID = m.Mill_ID
        WHERE l.Mill_ID = ?
        GROUP BY s.Stage_ID, s.Water_Stage, m.Mill_Name
        """
        cursor.execute(query, mill_id)
        results = cursor.fetchall()
        print(f"Raw results for mill_id {mill_id}:", results)  # Debug print
        return [{'Stage_ID': row.Stage_ID, 'Water_Stage': row.Water_Stage, 'Mill_Name': row.Mill_Name, 'Total_Stage_Value': row.Total_Stage_Value} for row in results]
    except Exception as e:
        print(f"Error in get_stage_values: {str(e)}")  # Error logging
        return []
    finally:
        conn.close()

def create_figure(value, title):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'family': 'Courier New, monospace', 'size': 18, 'color': '#39FF14'}},
        number={'font': {'color': "#39FF14"}},
        gauge={
            'axis': {'range': [None, max(1000, value * 1.2)], 'tickwidth': 2, 'tickcolor': "#39FF14"},
            'bar': {'color': "#39FF14"},
            'bgcolor': "rgba(0, 0, 0, 0)",
            'borderwidth': 2,
            'bordercolor': "#39FF14",
            'steps': [
                {'range': [0, value * 0.25], 'color': "rgba(0, 50, 0, 0.5)"},
                {'range': [value * 0.25, value * 0.5], 'color': "rgba(0, 100, 0, 0.5)"},
                {'range': [value * 0.5, value * 0.75], 'color': "rgba(0, 150, 0, 0.5)"},
                {'range': [value * 0.75, value], 'color': "rgba(0, 200, 0, 0.5)"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    fig.update_layout(
        width=360, 
        height=320,
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        font={'color': "#39FF14", 'family': "Courier New, monospace"},
        margin=dict(l=30, r=30, t=50, b=30)
    )
    return {
        'html': pio.to_html(fig, full_html=False, include_plotlyjs=False),
        'data': fig.to_json()
    }

@dash_bp.route('/update_view')
def update_view():
    view = request.args.get('view', 'view1')
    
    figures = {}

    print(f"Updating view: {view}")  # Debug print

    if view not in ['view1', 'view2', 'view3']:
        print(f"Unhandled view in update_view: {view}")
        return jsonify({'status': 'error', 'message': f'Unhandled view: {view}'})

    mills = ['1', '2', '3']

    if view == 'view1':
        for mill_id in mills:
            end_values = get_end_values(mill_id)
            figures[mill_id] = []
            for entry in end_values:
                end_value = entry['Total_End_Value']
                title = f"{entry['Mill_Name']} - {entry['Product_Name']} End Value"
                figures[mill_id].append(create_figure(end_value, title))
    elif view == 'view2':
        for mill_id in mills:
            stage_values = get_stage_values(mill_id)
            figures[mill_id] = []
            for entry in stage_values:
                stage_value = entry['Total_Stage_Value']
                title = f"{entry['Mill_Name']} - {entry['Water_Stage']} Stage Value"
                figures[mill_id].append(create_figure(stage_value, title))
    elif view == 'view3':
        for mill_id in mills:
            transfer_values = get_transfer_values(mill_id)
            figures[mill_id] = []
            for entry in transfer_values:
                transfer_value = entry['Total_End_Value']
                title = f"{entry['Mill_Name']} - {entry['Transfer_Type']} Transfer Value"
                figures[mill_id].append(create_figure(transfer_value, title))

    print(f"Generated figures for {view}:", figures)  # Debug print
    return jsonify({'status': 'success', 'view': view, 'figures': figures})

@dash_bp.route('/dash')
def render_dash():
    view = request.args.get('view', 'view1')
    figures = {}
    mills = ['1', '2', '3']

    if view == 'view1':
        for mill_id in mills:
            end_values = get_end_values(mill_id)
            figures[mill_id] = []
            for entry in end_values:
                end_value = entry['Total_End_Value']
                title = f"{entry['Mill_Name']} - {entry['Product_Name']} End Value"
                figures[mill_id].append(create_figure(end_value, title)['html'])
    elif view == 'view2':
        for mill_id in mills:
            stage_values = get_stage_values(mill_id)
            figures[mill_id] = []
            for entry in stage_values:
                stage_value = entry['Total_Stage_Value']
                title = f"{entry['Mill_Name']} - {entry['Water_Stage']} Stage Value"
                figures[mill_id].append(create_figure(stage_value, title)['html'])
    elif view == 'view3':
        for mill_id in mills:
            transfer_values = get_transfer_values(mill_id)
            figures[mill_id] = []
            for entry in transfer_values:
                transfer_value = entry['Total_End_Value']
                title = f"{entry['Mill_Name']} - {entry['Transfer_Type']} Transfer Value"
                figures[mill_id].append(create_figure(transfer_value, title)['html'])
    else:
        for mill_id in mills:
            figures[mill_id] = ["<p>Placeholder for View 2</p>"]

    return render_template('dash.html', figures=figures, initial_view=view)
