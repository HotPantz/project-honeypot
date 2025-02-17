import logging
import select
import socket
import threading
import paramiko
import time
import os
import signal
import sys
import subprocess
import pymysql
import pty
import requests
import pwd
import pam
from dotenv import load_dotenv

# For soft shutdown with CTRL+C
shutdown_requested = False

# Load host key and environment variable
HOST_KEY = paramiko.RSAKey(filename='key/serv_rsa.key')
CONNECTIONS_FILE = 'connections.json'

# Load .env file
load_dotenv()
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
    raise EnvironmentError("Missing required database environment variables")

class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()
        self.pam_auth = pam.pam()
        self.ip = 'unknown'  # default if not set externally

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # Log each login attempt.
        log_login_attempt(self.ip, username, password)
        # we use a custom PAM service set up with "pam_service_setup.sh"
        if self.pam_auth.authenticate(username, password, service='honeypot'):
            print(f"PAM authentication successful for user: {username}")
            return paramiko.AUTH_SUCCESSFUL
        else:
            print(f"PAM authentication failed for user: {username} - {self.pam_auth.reason}")
            return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password'

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def log_connection(ip, pseudo_id, duration):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO connections (ip, pseudo_id, duration, status) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (ip, pseudo_id, duration, True))  # Set status to True (online)
            connection.commit()
            return cursor.lastrowid  # Return the ID of inserted connection
    except pymysql.Error as e:
        logging.error(f"Database error: {e}")
        raise
    finally:
        connection.close()

def update_connection_status(connection_id, status):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE connections SET status = %s WHERE id = %s"
            cursor.execute(sql, (status, connection_id))
        connection.commit()
    except pymysql.Error as e:
        logging.error(f"Database error: {e}")
        raise
    finally:
        connection.close()

def update_connection_duration(connection_id, duration):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE connections SET duration = %s WHERE id = %s"
            cursor.execute(sql, (duration, connection_id))
        connection.commit()
    except pymysql.Error as e:
        logging.error(f"Database error: {e}")
        raise
    finally:
        connection.close()

def log_command(connection_id, command):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO user_commands (connection_id, command) VALUES (%s, %s)"
            cursor.execute(sql, (connection_id, command))
        connection.commit()
    finally:
        connection.close()

def log_login_attempt(ip, username, password):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO login_attempts (ip, username, password) VALUES (%s, %s, %s)"
            cursor.execute(sql, (ip, username, password))
        connection.commit()
    finally:
        connection.close()

# Starts fshell, logs the connection and its info, and logs the commands in the db
def handle_connection(client, addr):
    transport = paramiko.Transport(client)
    transport.add_server_key(HOST_KEY)
    server = Server()
    server.ip = addr[0]  # pass connection IP for logging
    try:
        transport.start_server(server=server)
    except paramiko.SSHException:
        print('SSH negotiation failed.')
        return

    chan = transport.accept(20)
    if chan is None:
        print('No channel.')
        return

    ip = addr[0]
    if ip == '127.0.0.1':  # For debugging/local testing.
        ip = '81.65.147.189'
    print(f'Authenticated connection from {ip}')
    
    pseudo_id = str(time.time())  # TODO: re-use same ID for the same IP if desired.
    start_time = time.time()
    
    try:
        connection_id = log_connection(ip, pseudo_id, 0)
        print(f"New connection logged with ID: {connection_id}")
        threading.Thread(target=update_ip_geolocation, args=(ip,)).start()

        username = transport.get_username()
        try:
            user_home = pwd.getpwnam(username).pw_dir
        except KeyError:
            user_home = os.path.expanduser("~")
        print(f"User '{username}' home directory: {user_home}")
        
        shell_path = os.path.abspath('../shell-emu/bin/fshell')
        master_fd, slave_fd = pty.openpty()
        shell_process = subprocess.Popen(
            [shell_path],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=user_home,
            close_fds=True
        )
        os.close(slave_fd)

        cmd_buffer = b""

        while not shutdown_requested:
            rlist, _, _ = select.select([master_fd, chan], [], [], 0.1)

            if master_fd in rlist:
                try:
                    output = os.read(master_fd, 1024)
                    if output:
                        chan.send(output)
                    else:
                        break  # Shell process may have finished
                except OSError:
                    break

            if chan in rlist:
                try:
                    data = chan.recv(1024)
                    if data:
                        os.write(master_fd, data)
                        cmd_buffer += data

                        if cmd_buffer.endswith(b'\n') or cmd_buffer.endswith(b'\r'):
                            lines = cmd_buffer.decode('utf-8', errors='ignore').splitlines()
                            for line in lines:
                                line = line.strip()
                                if line:
                                    log_command(connection_id, line)
                            cmd_buffer = b""
                    else:
                        break
                except Exception:
                    break

            if shell_process.poll() is not None:
                break

    except Exception as e:
        print(f'Connection error: {e}')
    finally:
        if shell_process.poll() is None:
            shell_process.terminate()
        duration = int(time.time() - start_time)
        print(f'Connection from {addr[0]} closed after {duration} seconds')
        update_connection_duration(connection_id, duration)
        update_connection_status(connection_id, False)  # Set status to False (offline)
        chan.close()
        transport.close()

def fetch_geolocation(ip):
    url = f"http://ip-api.com/json/{ip}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('status') == 'success':
            return {
                'country': data.get('country'),
                'country_code': data.get('countryCode'),
                'region': data.get('regionName'),
                'city': data.get('city'),
                'lat': data.get('lat'),
                'lon': data.get('lon')
            }
    except Exception as e:
        print("Error fetching geolocation:", e)
    return None

def update_ip_geolocation(ip):
    if ip == '127.0.0.1':
        ip = '81.65.147.189'
    print(ip)

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM ip_geolocations WHERE ip = %s ORDER BY fetched_at DESC LIMIT 1"
            cursor.execute(sql, (ip,))
            result = cursor.fetchone()
            if result:
                return result
            geo = fetch_geolocation(ip)
            if geo:
                insert_sql = """
                    INSERT INTO ip_geolocations (ip, country, country_code, region, city, lat, lon)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (ip, geo['country'], geo['country_code'], geo['region'], geo['city'], geo['lat'], geo['lon']))
                connection.commit()
                return geo
        return None
    finally:
        connection.close()

def signal_handler(signum, frame):
    global shutdown_requested
    print("\nShutdown requested...")
    shutdown_requested = True

def start_ssh_server():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 2222))
    server_socket.listen(100)
    print('Server started')
    
    while not shutdown_requested:
        try:
            server_socket.settimeout(1.25)  # check shutdown flag every 1.25s
            client, addr = server_socket.accept()
            print(f'Connection from {addr}')
            threading.Thread(target=handle_connection, args=(client, addr)).start()
        except socket.timeout:
            continue
        except Exception as e:
            print(f'Error: {e}')
            break
    
    print("Shutting down server...")
    server_socket.close()
    print("Done!")
    sys.exit(0)

if __name__ == '__main__':
    start_ssh_server()