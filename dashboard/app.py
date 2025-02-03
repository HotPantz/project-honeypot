from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import pymysql
import os
from dotenv import load_dotenv

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
    # Implement as needed using MariaDB queries or file reading
    if not os.path.exists('../logs/honeypot.log'):
        return jsonify([])
    with open('../logs/honeypot.log', 'r') as f:
        logs = f.readlines()
    max_lines = 50  # Adjust as needed
    logs = logs[-max_lines:]
    return jsonify(logs)

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

@app.route('/new_command', methods=['POST'])
def new_command():
    data = request.get_json()
    ip = data.get('ip')
    pseudo_id = data.get('pseudo_id')
    command = data.get('command')
    timestamp = data.get('timestamp')
    # Optionally: persist this command event in a separate table, e.g. command_emits,
    # if you need to persist real-time events independently.
    emit_new_command(ip, pseudo_id, command, timestamp)
    return jsonify({'status': 'success'})

# Function to emit new command logs to connected dashboard clients
def emit_new_command(ip, pseudo_id, command, timestamp):
    socketio.emit('new_command', {
        'ip': ip,
        'pseudo_id': pseudo_id,
        'command': command,
        'timestamp': timestamp
    })

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)