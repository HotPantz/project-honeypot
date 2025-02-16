from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import pymysql
import os
import glob
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re

app = Flask(__name__)
socketio = SocketIO(app)

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../.env'))
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    pass

init_db()

# Route for the dashboard. The navbar now only contains Dashboard and Live Shell.
@app.route('/')
def index():
    return render_template('index.html')

# New route for Live Shell page that queries the database for distinct IPs.
@app.route('/live_shell')
def live_shell():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Get distinct IPs and the latest timestamp for each.
            sql = """
                SELECT ip, MAX(timestamp) as last_seen
                FROM connections
                GROUP BY ip
                ORDER BY last_seen DESC;
            """
            cursor.execute(sql)
            shells = cursor.fetchall()
        # Define a threshold to consider an IP as 'online' (5 minutes).
        threshold = datetime.now() - timedelta(minutes=5)
        for shell in shells:
            # Convert last_seen to a datetime object if necessary.
            if isinstance(shell['last_seen'], str):
                shell['last_seen'] = datetime.strptime(shell['last_seen'], '%Y-%m-%d %H:%M:%S')
            shell['online'] = True if shell['last_seen'] >= threshold else False
        return render_template('live_shell.html', shells=shells)
    finally:
        connection.close()

# Route to access the live shell of a specific IP.
@app.route('/live_shell/<ip>')
def shell_detail(ip):
    return render_template('shell_detail.html', ip=ip)

# /live route now returns an empty list (no history displayed)
@app.route('/live')
def get_live():
    return jsonify([])

# Fetching connections & geolocation data from the database
@app.route('/connections')
def get_connections():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT c.*, g.country, g.country_code, g.region, g.city, g.lat, g.lon
                FROM connections c
                LEFT JOIN ip_geolocations g ON c.ip = g.ip
                ORDER BY c.timestamp DESC
                LIMIT 50
            """
            cursor.execute(sql)
            connections = cursor.fetchall()
        return jsonify(connections)
    finally:
        connection.close()

# Fetching the commands from the database
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

@app.route('/connections_over_time')
def connections_over_time():
    group_by = request.args.get('group_by', 'hour')
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if group_by == 'hour':
                sql = """
                    SELECT DATE_FORMAT(timestamp, '%Y-%m-%d') as period, COUNT(*) as count
                    FROM connections
                    GROUP BY period
                    ORDER BY period ASC;
                """
            else:
                sql = """
                    SELECT DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00') as period, COUNT(*) as count
                    FROM connections
                    GROUP BY period
                    ORDER BY period ASC;
                """
            cursor.execute(sql)
            data = cursor.fetchall()
        return jsonify(data)
    finally:
        connection.close()

# New route for Stats
@app.route('/stats')
def stats():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Get the 10 most popular commands
            popular_cmd_query = """
                SELECT command, COUNT(*) AS count
                FROM user_commands
                GROUP BY command
                ORDER BY count DESC
                LIMIT 10;
            """
            cursor.execute(popular_cmd_query)
            popular_commands = cursor.fetchall()
            
            # Calculate the average session duration
            avg_duration_query = "SELECT AVG(duration) AS avg_duration FROM connections;"
            cursor.execute(avg_duration_query)
            avg_duration = cursor.fetchone()  # This returns a dict with key 'avg_duration'
            
        return render_template('stats.html',
                               popular_commands=popular_commands,
                               avg_duration=avg_duration['avg_duration'])
    finally:
        connection.close()

# Modified emit_new_live function to include the ip associated with the log line.
def emit_new_live(log_line, ip=""):
    socketio.emit('new_live', {'log': log_line, 'ip': ip})

# Dictionary to track file offsets per file (only new content is processed)
file_offsets = {}

class LogFileEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            file_offsets[event.src_path] = 0

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            if event.src_path not in file_offsets:
                file_offsets[event.src_path] = 0
            offset = file_offsets.get(event.src_path, 0)
            try:
                with open(event.src_path, 'r') as f:
                    f.seek(offset)
                    new_lines = f.readlines()
                    file_offsets[event.src_path] = f.tell()
                    for line in new_lines:
                        # Ignore commented lines.
                        if line.strip().startswith("//"):
                            continue

                        # Check if the line contains "disconnected" (case insensitive)
                        if "disconnected" in line.lower():
                            # Attempt to extract the IP from the line
                            match = re.search(r'User ([\d\.]+)', line)
                            if match:
                                ip = match.group(1)
                            else:
                                # If not found in the line, extract the IP from the session log filename
                                file_match = re.search(r'session_([\d\.]+)_', event.src_path)
                                ip = file_match.group(1) if file_match else ""
                            print("Deconnexion detected:", line.strip(), "IP:", ip)
                            emit_new_live(line.strip(), ip)
                        else:
                            parts = line.strip().split(',')
                            if len(parts) >= 3:
                                timestamp_str, ip = parts[0], parts[1]
                                command = ",".join(parts[2:])
                                formatted = f"[{timestamp_str}] {ip}: {command}"
                                emit_new_live(formatted, ip)
            except Exception:
                pass

def start_log_watcher():
    logs_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../logs')
    for log_file in glob.glob(os.path.join(logs_folder, "*.txt")):
        try:
            with open(log_file, "r") as f:
                f.seek(0, os.SEEK_END)
                file_offsets[log_file] = f.tell()
        except Exception:
            file_offsets[log_file] = 0

    event_handler = LogFileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, logs_folder, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    socketio.start_background_task(start_log_watcher)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)