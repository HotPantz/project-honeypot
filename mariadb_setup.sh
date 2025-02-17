#!/bin/bash
set -e

# -----------------------------------------------------------------------------
# MariaDB Setup Script
#
# This script initializes the MariaDB database, creates a dedicated technical 
# user, and sets up the necessary tables 
# 
# IMPORTANT:
# CHANGE THE PASSWORD IN DB_PASSWORD VARIABLE
#
# Usage:
#   sudo bash mariadb_setup.sh
#
# -----------------------------------------------------------------------------

DB_NAME="honeypot_db"
DB_USER="honeypot_dbuser"
DB_PASSWORD="test#123"
SQL_SCRIPT="mariadb_tables.txt"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or use sudo"
    exit 1
fi

if ! command_exists mariadb; then
    echo "MariaDB is not installed. Please install MariaDB first."
    exit 1
fi

if [ ! -d /var/lib/mysql/mysql ]; then
    echo "Initializing MariaDB data directory..."
    mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
    echo "MariaDB data directory initialized."
fi

echo "Starting and enabling MariaDB service..."
systemctl enable --now mariadb

echo "Creating database and user..."
mariadb --skip-ssl-verify-server-cert -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME};"
mariadb --skip-ssl-verify-server-cert -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';"
mariadb --skip-ssl-verify-server-cert -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';"
mariadb --skip-ssl-verify-server-cert -e "FLUSH PRIVILEGES;"

echo "Importing table definitions..."
mariadb --skip-ssl-verify-server-cert ${DB_NAME} < ${SQL_SCRIPT}

echo "MariaDB setup completed successfully"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Please keep the password secure"