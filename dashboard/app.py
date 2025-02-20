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

LOGS_FOLDER = "/var/log/honeypot/"

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/live_shell')
def live_shell():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    c.ip,
                    MAX(c.timestamp) as last_seen,
                    g.country,
                    g.country_code,
                    g.city,
                    (SELECT status FROM connections WHERE ip = c.ip ORDER BY timestamp DESC LIMIT 1) as status
                FROM connections c
                LEFT JOIN ip_geolocations g ON c.ip = g.ip
                GROUP BY c.ip, g.country, g.country_code, g.city
                ORDER BY last_seen DESC;
            """
            cursor.execute(sql)
            shells = cursor.fetchall()
        
        for shell in shells:
            if isinstance(shell['last_seen'], str):
                shell['last_seen'] = datetime.strptime(shell['last_seen'], '%Y-%m-%d %H:%M:%S')
            shell['online'] = shell['status']  # Utiliser le statut de la base de données
            
            # Compter les commandes dans le dernier fichier de session
            logs_dir = LOGS_FOLDER
            session_files = [f for f in os.listdir(logs_dir) if f.startswith(f"session_{shell['ip']}_")]
            if session_files:
                session_files.sort(reverse=True)
                session_path = os.path.join(logs_dir, session_files[0])
                try:
                    with open(session_path, 'r') as f:
                        commands = f.readlines()
                    shell['command_count'] = len(commands)
                except Exception as e:
                    shell['command_count'] = 0
            else:
                shell['command_count'] = 0

        return render_template('live_shell.html', shells=shells)
    finally:
        connection.close()

@app.route('/live_shell/<ip>')
def shell_detail(ip):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    c.ip,
                    MAX(c.timestamp) as last_seen,
                    g.country,
                    g.country_code,
                    g.city,
                    (SELECT status FROM connections WHERE ip = c.ip ORDER BY timestamp DESC LIMIT 1) as status
                FROM connections c
                LEFT JOIN ip_geolocations g ON c.ip = g.ip
                WHERE c.ip = %s
                GROUP BY c.ip, g.country, g.country_code, g.city
            """
            cursor.execute(sql, (ip,))
            result = cursor.fetchone()
        if result:
            if isinstance(result['last_seen'], str):
                result['last_seen'] = datetime.strptime(result['last_seen'], '%Y-%m-%d %H:%M:%S')
            result['online'] = result['status']  # Utiliser le statut de la base de données
        return render_template('shell_detail.html', ip=ip, details=result)
    finally:
        connection.close()

@app.route('/live_content/<ip>')
def live_content(ip):
    logs_dir = LOGS_FOLDER
    session_files = [f for f in os.listdir(logs_dir) if f.startswith(f"session_{ip}_")]
    if not session_files:
        return jsonify({"content": ""})
    session_files.sort(reverse=True)
    session_path = os.path.join(logs_dir, session_files[0])
    try:
        with open(session_path, 'r') as f:
            content = f.read()
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"content": "", "error": str(e)})

@app.route('/live')
def get_live():
    return jsonify([])

@app.route('/connection_ips')
def get_connection_ips():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT DISTINCT ip FROM connections ORDER BY timestamp DESC;"
            cursor.execute(sql)
            ips = cursor.fetchall()
        return jsonify([row['ip'] for row in ips])
    finally:
        connection.close()

@app.route('/connections')
def get_connections():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    c.id,
                    c.ip,
                    c.timestamp,
                    c.duration,
                    g.country,
                    g.country_code,
                    g.region,
                    g.city,
                    g.lat,
                    g.lon
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

@app.route('/active_connections_count')
def active_connections_count():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT COUNT(DISTINCT ip) as count 
                FROM connections 
                WHERE status = 1;
            """
            cursor.execute(sql)
            result = cursor.fetchone()
        return jsonify(count=result['count'])
    finally:
        connection.close()

def background_active_connections_update():
    while True:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                    SELECT COUNT(DISTINCT ip) as count 
                    FROM connections 
                    WHERE status = 1;
                """
                cursor.execute(sql)
                result = cursor.fetchone()
                count = result['count']
        except Exception:
            count = 0
        finally:
            connection.close()
        socketio.emit('active_connections_update', {'count': count})
        time.sleep(10)  # update every 10 seconds

#status update receive from the ssh server for the live shell and shell detail pages
@app.route('/notify_status', methods=['POST'])
def notify_status():
    data = request.get_json()
    socketio.emit('status_update', data)
    return jsonify(success=True)

@app.route('/connections_over_time')
def connections_over_time():
    group_by = request.args.get('group_by', 'hour')
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if group_by == 'hour':
                sql = """
                    SELECT DATE_FORMAT(timestamp, '%H') as period, COUNT(*) as count
                    FROM connections
                    GROUP BY period
                    ORDER BY period ASC;
                """
            else: #default is day
                sql = """
                    SELECT DATE_FORMAT(timestamp, '%Y-%m-%d') as period, COUNT(*) as count
                    FROM connections
                    GROUP BY period
                    ORDER BY period ASC;
                """
            cursor.execute(sql)
            data = cursor.fetchall()
        return jsonify(data)
    finally:
        connection.close()

@app.route('/stats')
def stats():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Récupérer les commandes les plus populaires
            popular_cmd_query = """
                SELECT command, COUNT(*) AS count
                FROM user_commands
                GROUP BY command
                ORDER BY count DESC
                LIMIT 10;
            """
            cursor.execute(popular_cmd_query)
            popular_commands = cursor.fetchall()
            
            # Récupérer la durée moyenne des sessions
            avg_duration_query = "SELECT AVG(duration) AS avg_duration FROM connections;"
            cursor.execute(avg_duration_query)
            avg_duration = cursor.fetchone()
            
            # Récupérer les mots de passe les plus populaires
            popular_passwords_query = """
                SELECT password, COUNT(*) AS count
                FROM login_attempts
                GROUP BY password
                ORDER BY count DESC
                LIMIT 10;
            """
            cursor.execute(popular_passwords_query)
            popular_passwords = cursor.fetchall()

            # Récupérer les noms d'utilisateur les plus tentés
            popular_usernames_query = """
                SELECT username, COUNT(*) AS count
                FROM login_attempts
                GROUP BY username
                ORDER BY count DESC
                LIMIT 10;
            """
            cursor.execute(popular_usernames_query)
            popular_usernames = cursor.fetchall()

            # Récupérer les informations géographiques des connexions
            geo_connections_query = """
                SELECT ip, country, city, lat, lon
                FROM ip_geolocations
                WHERE lat IS NOT NULL AND lon IS NOT NULL;
            """
            cursor.execute(geo_connections_query)
            geo_connections = cursor.fetchall()
            
        return render_template('stats.html',
                               popular_commands=popular_commands,
                               avg_duration=avg_duration['avg_duration'],
                               popular_passwords=popular_passwords,
                               popular_usernames=popular_usernames,
                               geo_connections=geo_connections)
    finally:
        connection.close()
        
def emit_new_live(log_line, ip=""):
    socketio.emit('new_live', {'log': log_line, 'ip': ip})

file_offsets = {}

class LogFileEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.txt'):
            file_offsets[event.src_path] = 0
            filename = os.path.basename(event.src_path)
            if filename.startswith("session_"):
                match = re.search(r'session_([\d\.]+)_', filename)
                if match:
                    ip = match.group(1)
                    socketio.emit('new_session', {'ip': ip})

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
                        if line.strip().startswith("//"):
                            continue

                        if "disconnected" in line.lower():
                            match = re.search(r'User ([\d\.]+)', line)
                            if match:
                                ip = match.group(1)
                            else:
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
    logs_folder = LOGS_FOLDER  # use the correct absolute path
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
    socketio.start_background_task(background_active_connections_update)
    socketio.start_background_task(start_log_watcher)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)