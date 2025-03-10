import logging
import argparse
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
import pwd, grp
import pam
from dotenv import load_dotenv

#logging to file with date and time.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="server.log",    # Log file (relative or absolute path)
    filemode="a"              # Append mode
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

#For soft shutdown with CTRL+C
shutdown_requested = False

HOST_KEY = paramiko.RSAKey(filename='key/serv_rsa.key')

load_dotenv()
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

DASHBOARD_URL = os.getenv('DASHBOARD_URL', 'http://localhost:5000')  # default: localhost:5000
LOG_DIR = os.getenv('LOG_DIR', '/var/log/analytics')  # default: /var/log/analytics

if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DASHBOARD_URL]):
    raise EnvironmentError("Missing required database environment variables")

class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()
        self.pam_auth = pam.pam()
        self.ip = 'unknown'  #default if not set externally

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        original_username = username #storing the original username for logging
        if username == "root":
            username = "froot"
            logging.info(f"Redirecting root user to {username}")

        if ALLOW_ROOT and original_username == "root": #automatically accept all root connections
            logging.info("ALLOW_ROOT mode enabled: accepting authentication for root for user: " + original_username)
            log_login_attempt(self.ip, original_username, password, True)
            logging.info(f"PAM authentication successful for user: {original_username}")
            return paramiko.AUTH_SUCCESSFUL
        else: #use PAM authentication for non-root (or redirected root) users
            if self.pam_auth.authenticate(username, password, service='honeypot'):
                logging.info(f"PAM authentication successful for user: {username}")
                result = paramiko.AUTH_SUCCESSFUL
            else:
                logging.error(f"PAM authentication failed for user: {username} - {self.pam_auth.reason}")
                result = paramiko.AUTH_FAILED

            log_login_attempt(self.ip, username, password, result == paramiko.AUTH_SUCCESSFUL)
            return result

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
            cursor.execute(sql, (ip, pseudo_id, duration, True))  #setting the status to true for the dashboard to read it
            connection.commit()
            return cursor.lastrowid  #returning the ID of the new connection
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

def log_login_attempt(ip, username, password, success):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO login_attempts (ip, username, password, status) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (ip, username, password, success))
        connection.commit()
    finally:
        connection.close()

def drop_privileges(uid_name, gid_name):
    #security measure to run as non-root user
    if os.getuid() != 0:
        return

    try:
        running_uid = pwd.getpwnam(uid_name).pw_uid
        running_gid = grp.getgrnam(gid_name).gr_gid
    except KeyError as e:
        raise Exception(f"User or group {uid_name} not found: {e}")

    os.setgid(running_gid)
    os.setgroups([]) #remove all additional groups
    os.setuid(running_uid)
    os.umask(0o077) #set restrictive file creation mask

def handle_connection(client, addr):
    transport = paramiko.Transport(client)
    transport.add_server_key(HOST_KEY)
    server = Server()
    server.ip = addr[0]  #passing connection IP for logging
    
    transport.banner_timeout = 15 
    transport.auth_timeout = 30
    
    try:
        transport.start_server(server=server)
    except (paramiko.SSHException, EOFError) as e:
        logging.error(f'SSH negotiation failed: {str(e)}')
        transport.close()
        client.close()
        return

    chan = transport.accept(20)
    if chan is None:
        logging.error('No channel.')
        return

    ip = addr[0]
    username = transport.get_username()
    logging.info(f'Authenticated connection from {ip} as {username}')

    #ensuring root user is redirected to froot
    if username == "root":
        username = "froot"
        logging.info(f"Redirecting root user to {username}")

    #notifying the dashboard about new connection
    try:
        requests.post(f"{DASHBOARD_URL}/notify_status", json={'ip': ip, 'online': True}, timeout=10)
    except Exception as e:
        logging.error(f"Error notifying status update: {e}")

    pseudo_id = str(time.time())
    start_time = time.time()
    
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        connection_id = log_connection(ip, pseudo_id, 0)
        logging.info(f"New connection logged with ID: {connection_id}")
        #threading.Thread(target=update_ip_geolocation, args=(ip,)).start()
        update_ip_geolocation(ip) #trying in the main thread

        try:
            user_home = pwd.getpwnam(username).pw_dir
        except KeyError:
            user_home = os.path.expanduser("~")
        logging.info(f"User home directory: {user_home}")

        env = os.environ.copy()
        env["SSH_CLIENT_IP"] = ip #passing client IP to shell environment
        env["LOG_DIR"] = LOG_DIR

        shell_path = os.path.abspath('/usr/bin/fshell')
        master_fd, slave_fd = pty.openpty() #create pseudo-terminal for shell interaction

        env = os.environ.copy()
        env["SSH_CLIENT_IP"] = ip

        #launching fshell with dropped privileges
        shell_process = subprocess.Popen(
            [shell_path],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=user_home,
            env=env,
            preexec_fn=lambda: drop_privileges(username, username),
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
                        break
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
        logging.error(f'Connection error: {e}')
    finally:
        if shell_process.poll() is None:
            shell_process.terminate()
        duration = int(time.time() - start_time)
        logging.info(f'Connection from {addr[0]} closed after {duration} seconds')
        update_connection_duration(connection_id, duration)
        update_connection_status(connection_id, False)  # offline
        chan.close()
        transport.close()
        try:
            requests.post(f"{DASHBOARD_URL}/notify_status", json={'ip': ip, 'online': False}, timeout=10)
        except Exception as e:
            logging.error(f"Error notifying status update: {e}")

def fetch_geolocation(ip):
    url = f"http://ip-api.com/json/{ip}"
    try:
        response = requests.get(url, timeout=5)
        #handling rate limiting from the API
        remaining = response.headers.get("X-Rl")
        ttl = response.headers.get("X-Ttl")
        if remaining is not None and int(remaining) == 0:
            logging.info(f"Rate limit reached for IP-API. Please wait {ttl} seconds until the limit resets.")
            return None

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
        logging.error(f"Error fetching geolocation: {e}")
    return None

def update_ip_geolocation(ip):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            #check if we already have recent data for this IP
            sql = "SELECT * FROM ip_geolocations WHERE ip = %s ORDER BY fetched_at DESC LIMIT 1"
            cursor.execute(sql, (ip,))
            result = cursor.fetchone()
            
            fetch_new = False
            if result:
                #only update geolocations older than 1 day to avoid API rate limits
                record_time = result.get('fetched_at')
                if record_time is None or record_time < datetime.now() - timedelta(days=1):
                    fetch_new = True
                else:
                    logging.info(f"Geolocation for {ip} is recent; not updating.")
            else:
                fetch_new = True

            if fetch_new:
                logging.info(f"Fetching geolocation for {ip}.")
                geo = fetch_geolocation(ip)
                if geo:
                    if result: #update existing record
                        update_sql = """
                            UPDATE ip_geolocations 
                            SET country = %s,
                                country_code = %s,
                                region = %s,
                                city = %s,
                                lat = %s,
                                lon = %s,
                                fetched_at = NOW()
                            WHERE ip = %s
                        """
                        cursor.execute(update_sql, (
                            geo.get('country'),
                            geo.get('country_code'),
                            geo.get('region'),
                            geo.get('city'),
                            geo.get('lat'),
                            geo.get('lon'),
                            ip
                        ))
                    else: #create new record
                        insert_sql = """
                            INSERT INTO ip_geolocations (ip, country, country_code, region, city, lat, lon)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(insert_sql, (
                            ip,
                            geo.get('country'),
                            geo.get('country_code'),
                            geo.get('region'),
                            geo.get('city'),
                            geo.get('lat'),
                            geo.get('lon')
                        ))
                    connection.commit()
                    return geo
                else:
                    logging.error(f"Failed to fetch geolocation for {ip}.")
                    return None
            else:
                return result
    finally:
        connection.close()

def signal_handler(signum, frame):
    global shutdown_requested
    logging.info("Shutdown requested...")
    shutdown_requested = True

def start_ssh_server():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # For example, bind to port 22 if you need a privileged port solution before forking.
    server_socket.bind(('0.0.0.0', 22))
    server_socket.listen(100)
    logging.info('Server started')
    
    while not shutdown_requested:
        try:
            server_socket.settimeout(1.25) #check shutdown flag periodically
            client, addr = server_socket.accept()
            logging.info(f'Connection from {addr}')
            pid = os.fork()
            if pid == 0:
                 #child process handles the connection
                server_socket.close() 
                try:
                    handle_connection(client, addr)
                finally:
                    client.close()
                    os._exit(0)
            else:
                #parent process continues accepting connections
                client.close()
                os.waitpid(-1, os.WNOHANG)
        except socket.timeout:
            continue
        except Exception as e:
            logging.error(f'Error: {e}')
            break
    
    logging.info("Shutting down server...")
    server_socket.close()
    logging.info("Done!")
    sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SSH Server for Honeypot")
    parser.add_argument("--allow-root", action="store_true",
                        help="If provided, accept all root connections automatically")
    args = parser.parse_args()

    ALLOW_ROOT = args.allow_root

    if ALLOW_ROOT:
        logging.info("ALLOW_ROOT mode enabled: all root connections will be accepted.")
    else:
        logging.info("ALLOW_ROOT mode disabled: normal authentication applies.")

    start_ssh_server()