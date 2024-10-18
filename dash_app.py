import dash
from dash import dcc, html
import plotly.graph_objs as go
import pyodbc

# Function to create a new database connection
def create_connection():
    connection_string = 'Driver={ODBC Driver 17 for SQL Server};Server=192.168.56.2;Database=PLC_BOT;UID=bunny;PWD=4500;'
    return pyodbc.connect(connection_string)

# Function to get the end value for a specific mill
def get_end_value(mill_id):
    conn = create_connection()
    cursor = conn.cursor()
    query = """
        SELECT TOP 1 End_Value
        FROM dbo.Product_Movement_Log
        WHERE Mill_ID = ?
        ORDER BY Log_ID DESC
    """
    cursor.execute(query, (mill_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

# Initialize the Dash app
app = dash.Dash(__name__, server=False)

# Define the layout
app.layout = html.Div([
    html.H1("Mill End Values"),
    dcc.Graph(
        id='gauge-mill-a',
        figure={
            'data': [go.Indicator(
                mode="gauge+number",
                value=get_end_value('1'),
                title={'text': "Mill A End Value"},
                gauge={'axis': {'range': [None, 100]}}
            )]
        }
    ),
    dcc.Graph(
        id='gauge-mill-b',
        figure={
            'data': [go.Indicator(
                mode="gauge+number",
                value=get_end_value('2'),
                title={'text': "Mill B End Value"},
                gauge={'axis': {'range': [None, 100]}}
            )]
        }
    ),
    dcc.Graph(
        id='gauge-mill-c',
        figure={
            'data': [go.Indicator(
                mode="gauge+number",
                value=get_end_value('3'),
                title={'text': "Mill C End Value"},
                gauge={'axis': {'range': [None, 100]}}
            )]
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)