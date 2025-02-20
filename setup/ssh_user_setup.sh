#!/bin/bash
# Creates a user for the honeypot and sets up the honeypot log directory

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

# Create user without a home directory and with custom shell
$SUDO useradd -m honeypot_user -d /home/honeypot_user -s /usr/bin/fshell

echo "Please set the password for honeypot_user:"
$SUDO passwd honeypot_user

# Create log directory and fix its permissions
$SUDO mkdir -p /var/log/honeypot
$SUDO chown -R honeypot_user:honeypot_user /var/log/honeypot
$SUDO chmod -R 0755 /var/log/honeypot