#!/bin/bash
set -e

# -----------------------------------------------------------------------------
# MariaDB Setup Script
#
# This script initializes the MariaDB database, creates a dedicated technical 
# user, and sets up the necessary tables.
#
# IMPORTANT:
# DB_NAME, DB_USER, and DB_PASSWORD values are read from ../.env.
#
# Usage:
#   sudo bash mariadb_setup.sh
#
# -----------------------------------------------------------------------------

# Load environment variables from ../.env
if [ -f ../.env ]; then
    set -o allexport
    . ../.env
    set +o allexport
else
    echo ".env file not found in parent directory. Please create ../.env with required DB_XX values."
    exit 1
fi

# Check that required DB variables are set
if [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo "DB_NAME, DB_USER, or DB_PASSWORD are not set in ../.env"
    exit 1
fi

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
mariadb --skip-ssl-verify-server-cert -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';"
mariadb --skip-ssl-verify-server-cert -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';"
mariadb --skip-ssl-verify-server-cert -e "FLUSH PRIVILEGES;"

echo "Importing table definitions..."
mariadb --skip-ssl-verify-server-cert ${DB_NAME} < ${SQL_SCRIPT}

echo "MariaDB setup completed successfully"
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Please keep the password secure"