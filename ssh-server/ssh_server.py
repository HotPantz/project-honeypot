import socket
import threading
import paramiko
import json
import time
import os
import sqlite3
import pymysql

HOST_KEY = paramiko.RSAKey(filename='test_rsa.key')
CONNECTIONS_FILE = 'connections.json'

# Initialize connections file
def init_connections_file():
    if not os.path.exists(CONNECTIONS_FILE):
        with open(CONNECTIONS_FILE, 'w') as f:
            json.dump([], f)

init_connections_file()

class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        return paramiko.AUTH_SUCCESSFUL

def log_connection(ip, pseudo_id, duration):
    connection = pymysql.connect(host=DB_HOST,
                                 user=DB_USER,
                                 password=DB_PASSWORD,
                                 database=DB_NAME)
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO connections (ip, pseudo_id, duration) VALUES (%s, %s, %s)"
            cursor.execute(sql, (ip, pseudo_id, duration))
        connection.commit()
    finally:
        connection.close()

def log_command(connection_id, command):
    connection = pymysql.connect(host=DB_HOST,
                                 user=DB_USER,
                                 password=DB_PASSWORD,
                                 database=DB_NAME)
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO user_commands (connection_id, command) VALUES (%s, %s)"
            cursor.execute(sql, (connection_id, command))
        connection.commit()
    finally:
        connection.close()

def handle_connection(client, addr):
    transport = paramiko.Transport(client)
    transport.add_server_key(HOST_KEY)
    server = Server()
    try:
        transport.start_server(server=server)
    except paramiko.SSHException:
        print('SSH negotiation failed.')
        return

    chan = transport.accept(20)
    if chan is None:
        print('No channel.')
        return

    print(f'Authenticated connection from {addr[0]}')
    
    # Log the connection and get the connection_id
    pseudo_id = "unique_session_id"  # Replace with actual logic to generate pseudo_id
    start_time = time.time()
    
    conn = sqlite3.connect('honeypot.db')
    c = conn.cursor()
    c.execute('INSERT INTO connections (ip, pseudo_id, duration) VALUES (?, ?, ?)', 
              (addr[0], pseudo_id, 0))
    connection_id = c.lastrowid
    conn.commit()
    conn.close()
    
    try:
        while True:
            if chan.recv_ready():
                command = chan.recv(1024).decode('utf-8').strip()
                if command:
                    log_command(connection_id, command)
    except Exception as e:
        print(f'Connection error: {e}')
    finally:
        duration = int(time.time() - start_time)
        log_connection(addr[0], pseudo_id, duration)
        chan.close()
        transport.close()

def start_ssh_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 2222))
    server_socket.listen(100)
    print('Listening for connection ...')

    while True:
        client, addr = server_socket.accept()
        print(f'Connection from {addr}')
        threading.Thread(target=handle_connection, args=(client, addr)).start()

if __name__ == '__main__':
    start_ssh_server()