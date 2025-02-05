from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import pymysql
import os
import glob
from datetime import datetime
import time
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
    log_lines = []
    # Calculate the logs path relative to the dashboard folder.
    logs_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../shell-emu/logs')
    if not os.path.exists(logs_folder):
        return jsonify([])

    # Gather all session log files (assumed to be prefixed with "shell_session_")
    pattern = os.path.join(logs_folder, "shell_session_*.txt")
    for log_file in glob.glob(pattern):
        with open(log_file, "r") as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    timestamp_str, ip = parts[0], parts[1]
                    # In case the command contains commas, rejoin remaining parts.
                    command = ",".join(parts[2:])
                    # Format the line (assuming timestamp format is sortable e.g. YYYY-MM-DD HH:MM:SS)
                    formatted = f"[{timestamp_str}] {ip}: {command}"
                    # Save both the parsed timestamp (for sorting) and the formatted line.
                    try:
                        ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        ts = datetime.min
                    log_lines.append((ts, formatted))
                else:
                    # Ignore or add raw line in case it doesn't follow the CSV structure.
                    continue

    # Sort by timestamp
    log_lines.sort(key=lambda x: x[0])
    # Extract only the formatted strings and select the last 50 entries
    formatted_lines = [line for _, line in log_lines][-50:]
    return jsonify(formatted_lines)

#fetching connections & geolocation data from the database
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

#fetching the commands from the database
@app.route('/commands')
def get_commands():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            #joining the commands with the connections table to get the ip and pseudo_id
            #and ordering by the latest
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
    group_by = request.args.get('group_by', 'hour','day')
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

def emit_new_live(log_line):
    socketio.emit('new_live', {'log': log_line})

# Dictionary to track file offsets per file so that we only read new content.
file_offsets = {}

class LogFileEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            # Open file and seek to last known offset.
            offset = file_offsets.get(event.src_path, 0)
            try:
                with open(event.src_path, 'r') as f:
                    f.seek(offset)
                    new_lines = f.readlines()
                    file_offsets[event.src_path] = f.tell()
                    for line in new_lines:
                        parts = line.strip().split(',')
                        if len(parts) >= 3:
                            timestamp_str, ip = parts[0], parts[1]
                            command = ",".join(parts[2:])
                            # Format the line.
                            formatted = f"[{timestamp_str}] {ip}: {command}"
                            emit_new_live(formatted)
            except Exception:
                # Silently ignore file reading errors.
                pass

def start_log_watcher():
    logs_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../logs')
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

# Start the log watcher in a background thread so that it keeps monitoring new lines.
socketio.start_background_task(start_log_watcher)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)