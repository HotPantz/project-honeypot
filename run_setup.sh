#!/bin/bash
#Sets up the Python virtual environment and runs all the setup scripts
read -p "Are you sure you  changed the password in .env and setup/mariadb_setup.sh? (y/n)" answer
if [[ ! "$answer" =~ ^[Yyyes]$ ]]; then
    echo "Aborting setup"
    exit 1
fi

echo "Setting up Python virtual environment..."
python -m venv .venv

echo "Activating virtual environment and installing Python dependencies..."
source .venv/bin/activate
pip install flask flask-socketio paramiko pymysql python-dotenv requests watchdog pam passlib six
echo "Done."

echo "Running setup scripts..."
cd ./setup/
sudo mariadb_setup.sh
sudo ssh_user_setup.sh
sudo pam_service_setup.sh
echo "Done."
cd ..

echo "Setting up SSH server RSA key..."
cd ./ssh-server/key/
sudo ssh-keygen -t rsa -b 2048 -f serv_rsa.key
echo "Done."
cd ../../

echo "Setup completed successfully"
echo "Please keep the password secure"