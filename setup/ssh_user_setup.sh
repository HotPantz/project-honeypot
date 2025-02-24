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

$SUDO useradd -m froot -d /home/froot -s /usr/bin/fshell

echo "Please set the password for froot:"
$SUDO passwd froot

# log dir with froot ownership
$SUDO mkdir -p "$LOG_DIR"
$SUDO chown froot:froot "$LOG_DIR"
$SUDO chmod 0775 "$LOG_DIR"
echo "Honeypot log directory created at $LOG_DIR"

#shared directory for fake command output files
$SUDO mkdir -p /usr/share/fshell
$SUDO cp -r "$(dirname "$0")/../shell-emu/resources/commands/"* /usr/share/fshell/
$SUDO chmod -R 755 /usr/share/fshell
echo "Shared fshell resources installed to /usr/share/fshell"