import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import sqlite3
import threading
import time
import os

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize database
def init_db():
    conn = sqlite3.connect('honeypot.db')
    c = conn.cursor()
    
    # Create connections table
    c.execute('''CREATE TABLE IF NOT EXISTS connections
                 (id INTEGER PRIMARY KEY, ip TEXT, pseudo_id TEXT, duration TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create command usage log table
    c.execute('''CREATE TABLE IF NOT EXISTS command_usage
                 (id INTEGER PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, command TEXT)''')
    
    # Create connection count log table
    c.execute('''CREATE TABLE IF NOT EXISTS connection_count
                 (id INTEGER PRIMARY KEY, ip TEXT, pseudo_id TEXT, connection_count INTEGER)''')
    
    conn.commit()
    conn.close()

init_db()

# Route for the dashboard
@app.route('/')
def index():
    return render_template('index.html')

# Route to get live shell output
@app.route('/live')
def get_live():
    with open('honeypot.log', 'r') as f:
        logs = f.readlines()
    return jsonify(logs)

# Route to get SSH connections
@app.route('/connections')
def get_connections():
    conn = sqlite3.connect('honeypot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM connections')
    connections = c.fetchall()
    conn.close()
    return jsonify(connections)

# Route to get command usage logs
@app.route('/command_usage')
def get_command_usage():
    conn = sqlite3.connect('honeypot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM command_usage')
    command_usage = c.fetchall()
    conn.close()
    return jsonify(command_usage)

# Route to get connection count logs
@app.route('/connection_count')
def get_connection_count():
    conn = sqlite3.connect('honeypot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM connection_count')
    connection_count = c.fetchall()
    conn.close()
    return jsonify(connection_count)

# Route to update SSH configuration
@app.route('/update_ssh', methods=['POST'])
def update_ssh():
    config = request.json
    # Update SSH configuration logic here
    return jsonify({'status': 'success'})

# Function to log SSH connections
def log_connection(ip, pseudo_id, duration):
    conn = sqlite3.connect('honeypot.db')
    c = conn.cursor()
    c.execute('INSERT INTO connections (ip, pseudo_id, duration) VALUES (?, ?, ?)', (ip, pseudo_id, duration))
    conn.commit()
    conn.close()
    socketio.emit('new_connection', {'ip': ip})

# Function to log command usage
def log_command_usage(command):
    conn = sqlite3.connect('honeypot.db')
    c = conn.cursor()
    c.execute('INSERT INTO command_usage (command) VALUES (?)', (command,))
    conn.commit()
    conn.close()

# Function to log connection count
def log_connection_count(ip, pseudo_id):
    conn = sqlite3.connect('honeypot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM connection_count WHERE ip = ? AND pseudo_id = ?', (ip, pseudo_id))
    row = c.fetchone()
    if row:
        c.execute('UPDATE connection_count SET connection_count = connection_count + 1 WHERE ip = ? AND pseudo_id = ?', (ip, pseudo_id))
    else:
        c.execute('INSERT INTO connection_count (ip, pseudo_id, connection_count) VALUES (?, ?, ?)', (ip, pseudo_id, 1))
    conn.commit()
    conn.close()

# Function to monitor live shell output and emit updates
def monitor_live():
    with open('honeypot.log', 'r') as f:
        f.seek(0, 2)  # Move to the end of the file
        while True:
            line = f.readline()
            if line:
                socketio.emit('new_live', {'log': line})
            time.sleep(1)

# Function to monitor connections file and emit updates
def monitor_connections():
    last_mtime = os.path.getmtime('connections.json')
    while True:
        current_mtime = os.path.getmtime('connections.json')
        if current_mtime != last_mtime:
            last_mtime = current_mtime
            with open('connections.json', 'r') as f:
                connections = json.load(f)
            socketio.emit('update_connections', connections)
        time.sleep(1)

# Start live shell output and connections monitoring in separate threads
threading.Thread(target=monitor_live).start()
threading.Thread(target=monitor_connections).start()

if __name__ == '__main__':
    socketio.run(app, debug=True)