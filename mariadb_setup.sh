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
DB_PASSWORD="<password>"


SQL_SCRIPT="mariadb_tables.txt"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as use sudo."
    exit 1
fi

# is the mariadb package installed?
if ! command_exists mariadb; then
    echo "MariaDB is not installed. Please install MariaDB first."
    exit 1
fi

# install mariadb
if [ ! -d /var/lib/mysql/mysql ]; then
    echo "Initializing MariaDB data directory..."
    mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
    echo "MariaDB data directory initialized."
else
    echo "MariaDB data directory already initialized."
fi

# Start and enable MariaDB service
echo "Starting and enabling MariaDB service..."
systemctl enable --now mariadb
echo "MariaDB service started and enabled."

# Secure MariaDB Installation (Optional but Recommended)
# You can uncomment the following lines to run the secure installation script
# echo "Running mysql_secure_installation..."
# mysql_secure_installation

# Create the Honeypot Database
echo "Creating database '$DB_NAME'..."
mysql -u root -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`;"
echo "Database '$DB_NAME' created or already exists."

# Create a Dedicated User for the Honeypot Project
echo "Creating MariaDB user '$DB_USER'..."
mysql -u root -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
echo "User '$DB_USER' created or already exists."

# Grant Necessary Privileges to the User
echo "Granting all privileges on '$DB_NAME' to '$DB_USER'..."
mysql -u root -e "GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';"
mysql -u root -e "FLUSH PRIVILEGES;"
echo "Privileges granted to '$DB_USER'."

# Check if the SQL script exists
if [ ! -f "$SQL_SCRIPT" ]; then
    echo "SQL script '$SQL_SCRIPT' not found. Please ensure the file exists."
    exit 1
fi

# Import Table Definitions into the Database
echo "Importing table definitions from '$SQL_SCRIPT'..."
mysql -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SQL_SCRIPT"
echo "Table definitions imported successfully."

# Final Message
echo "MariaDB setup for Honeypot project completed successfully."
echo "Database Name: $DB_NAME"
echo "Database User: $DB_USER"
echo "Database Password: $DB_PASSWORD"
echo "Please ensure to keep the password secure."