#!/bin/bash
# Creates a user for the honeypot and sets up the honeypot log directory

#load .env
if [ -f "../.env" ]; then
    set -a
    . ../.env
    set +a
else
    echo ".env file not found. Using defaults."
    LOG_DIR="/var/log/analytics"
fi

#building the fshell binary first
cd "$(dirname "$0")/../shell-emu"
make
cd "$(dirname "$0")"

# running sudo only if not root
if [ "$(id -u)" -ne 0 ]; then
    SUDO='sudo'
else
    SUDO=''
fi

$SUDO useradd -m admin -d /home/admin -s /usr/bin/fshell

echo "Please set the password for admin:"
$SUDO passwd admin

# log dir with root ownership, writeonly for admin
$SUDO mkdir -p "$LOG_DIR"
$SUDO chown root:admin "$LOG_DIR"
$SUDO chmod 0333 "$LOG_DIR"
echo "Honeypot log directory created at $LOG_DIR"

#shared directory for fake command output files
$SUDO mkdir -p /usr/share/fshell
$SUDO cp -r "$(dirname "$0")/../shell-emu/resources/commands/"* /usr/share/fshell/
$SUDO chmod -R 755 /usr/share/fshell
echo "Shared fshell resources installed to /usr/share/fshell"