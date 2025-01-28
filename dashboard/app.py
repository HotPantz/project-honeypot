import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import pymysql
import threading
import time
import os

app = Flask(__name__)
socketio = SocketIO(app)

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

# Database connection parameters
DB_HOST = 'localhost'
DB_USER = 'honeypot_user'
DB_PASSWORD = 'SecureP@ssw0rd'  # Use the password you set in mariadb_setup.sh
DB_NAME = 'honeypot_db'

def get_db_connection():
    return pymysql.connect(host=DB_HOST,
                           user=DB_USER,
                           password=DB_PASSWORD,
                           database=DB_NAME,
                           cursorclass=pymysql.cursors.DictCursor)

# Initialize database (tables are created via mariadb_setup.sh)
def init_db():
    pass

init_db()

# Route for the dashboard
@app.route('/')
def index():
    return render_template('index.html')

# Route to get live shell output
@app.route('/live')
def get_live():
    # Implement as needed using MariaDB queries or file reading
    if not os.path.exists('../logs/honeypot.log'):
        return jsonify([])
    with open('../logs/honeypot.log', 'r') as f:
        logs = f.readlines()
    max_lines = 50  # Adjust as needed
    logs = logs[-max_lines:]
    return jsonify(logs)

# Route to get SSH connections
@app.route('/connections')
def get_connections():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM connection_count ORDER BY timestamp DESC LIMIT 50"
            cursor.execute(sql)
            connections = cursor.fetchall()
        return jsonify(connections)
    finally:
        connection.close()

# Route to get command logs
@app.route('/commands')
def get_commands():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = '''
                SELECT uc.id, c.ip, c.pseudo_id, uc.command, uc.timestamp
                FROM user_commands uc
                JOIN connections c ON uc.connection_id = c.id
                ORDER BY uc.timestamp DESC
                LIMIT 100
            '''
            cursor.execute(sql)
            commands = cursor.fetchall()
        return jsonify(commands)
    finally:
        connection.close()

# Route to update SSH configuration (implement as needed)
@app.route('/update_ssh', methods=['POST'])
def update_ssh():
    config = request.json
    # Update SSH configuration logic here
    return jsonify({'status': 'success'})

# Function to emit new command logs
def emit_new_command(ip, pseudo_id, command, timestamp):
    socketio.emit('new_command', {
        'ip': ip,
        'pseudo_id': pseudo_id,
        'command': command,
        'timestamp': timestamp
    })

# You can add more functions and routes as needed

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)