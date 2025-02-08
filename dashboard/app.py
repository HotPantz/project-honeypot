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

def init_db():
    pass

init_db()

# Route for the dashboard
@app.route('/')
def index():
    return render_template('index.html')

# /live route now returns an empty list (no history displayed)
@app.route('/live')
def get_live():
    return jsonify([])

# fetching connections & geolocation data from the database
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

# fetching the commands from the database
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

def emit_new_live(log_line):
    socketio.emit('new_live', {'log': log_line})

# Dictionary to track file offsets per file (only new content is processed)
file_offsets = {}

class LogFileEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            # For new log files created after the app starts, start from beginning.
            file_offsets[event.src_path] = 0

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            # If for any reason the file is not yet tracked, assume new file and start at 0.
            if event.src_path not in file_offsets:
                file_offsets[event.src_path] = 0

            offset = file_offsets.get(event.src_path, 0)
            try:
                with open(event.src_path, 'r') as f:
                    f.seek(offset)
                    new_lines = f.readlines()
                    file_offsets[event.src_path] = f.tell()  # update offset to file's end
                    for line in new_lines:
                        # Skip comment lines starting with "//"
                        if line.strip().startswith("//"):
                            continue
                        parts = line.strip().split(',')
                        if len(parts) >= 3:
                            timestamp_str, ip = parts[0], parts[1]
                            command = ",".join(parts[2:])
                            formatted = f"[{timestamp_str}] {ip}: {command}"
                            emit_new_live(formatted)
            except Exception:
                pass

def start_log_watcher():
    logs_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../logs')
    
    # For each existing file, set its offset to the end (ignore historical logs)
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
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)