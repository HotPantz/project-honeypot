#!/bin/bash
#Sets up the Python virtual environment and runs all the setup scripts
python3 -c "import venv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Python venv module is not installed. Please install it (e.g., sudo apt install python3-venv)."
    exit 1
fi

read -p "Are you sure you changed the password in .env and/or setup/mariadb_setup.sh? (y/n) " answer
if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Aborting setup"
    exit 1
fi

read -p "Select installation type ([full] for full install with database and dashboard, [minimal] for shell and user setup only): " install_type
if [[ "$install_type" != "full" && "$install_type" != "minimal" ]]; then
    echo "Invalid option. Aborting setup."
    exit 1
fi

echo "Setting up Python virtual environment..."
python3 -m venv .venv

echo "Activating virtual environment and installing Python dependencies..."
source .venv/bin/activate
pip install flask flask-socketio paramiko pymysql python-dotenv requests watchdog pam passlib six
echo "Done."

echo "Building the shell..."
cd ./shell-emu
make
cd ..

echo "Running setup scripts..."
cd ./setup/

if [[ "$install_type" == "full" ]]; then
    sudo ./mariadb_setup.sh
fi

sudo ./pam_service_setup.sh
sudo ./ssh_user_setup.sh
echo "Done."
cd ..

echo "Setting up SSH server RSA key..."
cd ./ssh-server/key/
sudo ssh-keygen -t rsa -b 2048 -f serv_rsa.key -N ""
echo "Done."
cd ../../

echo "Setup completed successfully"
echo "Please keep the password secure"