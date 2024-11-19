import socket
import threading
import paramiko
import json
import time
import os
import sqlite3

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
    conn = sqlite3.connect('honeypot.db')
    c = conn.cursor()
    c.execute('INSERT INTO connections (ip, pseudo_id, duration) VALUES (?, ?, ?)', (ip, pseudo_id, duration))
    conn.commit()
    conn.close()

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

    # Log the connection
    pseudo_id = 'user123'  # Replace with actual pseudo ID logic
    duration = '5m'  # Replace with actual duration logic
    log_connection(addr[0], pseudo_id, duration)

    chan.send('Welcome to the honeypot!\n')
    chan.close()

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