# app.py (Flask Backend)
# This file contains the backend logic for the application.
# It defines the routes for the API endpoints and handles the data processing and database interactions.
# The backend is built using Flask, a Python web framework.
from flask import Flask, render_template, request, jsonify
import pyodbc
import logging
from flask_cors import CORS


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Set up logging
logging.basicConfig(level=logging.DEBUG)

#Importing the routes
from routes import routes
app.register_blueprint(routes)

from view_routes import view_routes
app.register_blueprint(view_routes)

from view_routes_transfers import view_routes_transfers
app.register_blueprint(view_routes_transfers)

from view_routes_water import view_routes_water
app.register_blueprint(view_routes_water)

# Importing and registering the dash module
from dash_module import dash_bp
app.register_blueprint(dash_bp)

from manage_tables import manage_tables_bp
app.register_blueprint(manage_tables_bp)




# Run the Flask app in debug mode if this file is run directly
if __name__ == '__main__':
    app.run(debug=True)


