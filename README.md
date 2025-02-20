# Project Honeypot

## Overview

**Project Honeypot** is a C++-based SSH honeypot designed to simulate an accessible shell, attracting and logging malicious attack attempts. The primary objective is to analyze attacker behavior while ensuring the security of the host system.

## Quick Navigation

- [Overview](#overview)
- [Features](#features)
- [File Structure](#file-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **SSH Server Simulation**: Emulates an open SSH server that provides an interactive shell without requiring authentication.
- **Command Simulation**: Supports basic shell commands such as `sudo`, `cd`, `ls`, and more.
- **Command Logging**: Records all executed commands into log files for detailed analysis of attacker activities.
- **Mini File System**: Implements a simplified file system structure, including support for the `wget` command.
- **User and Group Simulation**: Features commands like `whoami` to enhance the realism of the simulated environment.
- **Security Measures**: Designed to run within a virtual machine to ensure the host system remains protected from potential threats.

## Installation

### Prerequisites
1. #### Packets

    - **C++ Compiler**: Ensure you have a C++ compiler installed (e.g., `g++`). **Make sure you have the libcurl library installed !!**
    - **CMake**: Required for building the project.
    - **Python & Dependencies, Venv**: The server and dashboard are Python apps running in a Python Venv.
    - **VirtualBox** (optional): If you would like to run the app inside a VM for safety measures.

2. #### Environment Configuration

    - **Create a ```.env``` file** :

    In the project root directory, with the following lines : 
    ```
    DB_HOST=<IP>
    DB_USER=<USERNAME>
    DB_PASSWORD=<PASSWORD>
    DB_NAME=<NAME>
    DASHBOARD_URL=http://<IP>:<PORT>
    LOG_DIR=<BY DEFAULT : var/log/analytics>
    ```
    
    - **To connect to the DB (on a different host) from the VM** :
    
    Run this command on the DB (as root/any user with priveleges) :  
    ```sql
    GRANT ALL PRIVILEGES ON honeypot_db.* TO '<USER_DEFINED_MARIADB>'@'%' IDENTIFIED BY '<YOUR_PASSWORD>';
    ```
---

### Manual Installation/Setup

1. **Clone the Repository**

    ```bash
    git clone https://github.com/HotPantz/project-honeypot.git
    cd project-honeypot
    ```

2. **Build the shell**

    Navigate to the shell-emu directory and run:

    ```bash
    make
    ```

3. **Set Up the Environment**

    a. **Create and Activate a Python Virtual Environment**

    Create a virtual environment in the project root:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

    b. **Install Python Dependencies**

    With the virtual environment activated, install the required packages:

    ```bash
    pip install flask flask-socketio paramiko pymysql python-dotenv requests watchdog pam passlib six
    ```

    c. **Run Setup Scripts**

    Run the setup scripts individually:

    ```bash
    ./setup/mariadb_setup.sh
    ./setup/pam_service_setup.sh
    ./setup/ssh_user_setup.sh
    ```

    d. **Generate an RSA Key**

    Create an RSA key in the ```ssh-server/key``` directory:

    ```bash
    ssh-keygen -t rsa -b 2048 -f ssh-server/key/serv_rsa.key
    ```

    e. **VM ONLY : Test the DB connection from the Guest (if on a VM) to the host**

    ```bash
    mariadb -h HOST_IP -u USERNAME  -p
    ```
    
    f. **VM ONLY : Share the ```/var/log/honeypot``` folder through NFS with the host**

    Make sur you have the NFS server and clients on the VM and host respectively!

    1. Edit ```/etc/exports``` and add this line (replace the IP with your host machine's IP address):

    ```bash
    /var/log/honeypot <HOST_IP>(rw,sync,no_subtree_check,no_root_squash)
    ```
    2. Restart the NFS server

    3. On the host, mount the directory :
    ```bash
    sudo mount -t nfs -o rw,actimeo=0 <VM_IP>:/var/log/honeypot /var/log/honeypot
    ```

---

### Automated Setup

Alternatively, you can run the provided automated setup script, which runs all the necessary setup scripts for you:

1. **Clone the Repository**

    ```bash
    git clone https://github.com/HotPantz/project-honeypot.git
    cd project-honeypot
    ```

2. **Run the Automated Setup Script**

    Execute the run_setup.sh script by running:
    ```bash
    ./run_setup.sh
    ```

    The script will prompt you to confirm that the database passwords are updated in .env and mariadb_setup.sh before proceeding.

---

## Usage

### Setting it up

1. **Start the SSH Server**

    We need to run the server with sudo privileges to read ```/etc/shadow``` for password authentication with PAM:

    ```bash
    sudo ../.venv/bin/python ssh_server.py
    ```

2. **Launch the Dashboard**

    Start the Flask dashboard by navigating to the dashboard directory and running:

    ```bash
    python dashboard/app.py
    ```
    
    The app runs at ```http://localhost:5000``` by default, if no environment variable is specified.

3. **Monitor Activity**

    - All command logs generated by the honeypot are saved in the logs directory.
    - Analyze these log files to understand attacker behaviors and strategies.

4. **Configure Network Settings**

    - Forward the SSH port (default is 22) from your router to the IP address of the virtual machine running the honeypot.
    - Ensure that the honeypot is accessible from the internet to attract potential attackers.

### Adding fake-command-output files

In the ```shell-emu/resources``` folder, we provide you with some sample fake outputs of common commands (pstree, tree, ip)
They are supposed to be read from a shared location on the system, since we're executing the shell from ```/usr/bin```. You can 
easily add new commands by altering the switch:case code inside ```shell-emu/src/fshell.cpp```, and add new commands to be
fake-outputted. 
Their names are vague on purpose, but you can name them anything you want provided you change the code accordingly.

## File Structure

```
.
├── .env                        # Database configuration (host, username, db name, password)
├── .gitignore            
dashboard/                  # Flask dashboard
│   ├── app.py                  # Main app
│   ├── static/                 # Static assets for the dashboard (css)
│   └── templates/              # HTML pages
setup/
│   ├── mariadb_setup.sh        # MariaDB user, and database setup
│   ├── mariadb_tables.txt      # SQL commands for database tables
│   ├── pam_service_setup.sh    # PAM service config for authentication
│   └── ssh_user_setup.sh       # SSH user accounts setup
ssh-server/                 # SSH server & config
│   ├── key/
│   │   └── rsakey.dummy    # Contains the command to generate an RSA key for the server
│   └── ssh_server.py
shell-emu/
├── bin/
├── src/
│   ├── fshell.cpp
│   ├── shell_parser.cpp
│   ├── logger.cpp
│   └── main.cpp
├── headers/
│   ├── fshell.hpp
│   ├── shell_parser.hpp
│   └── logger.hpp
└── Makefile
TODO.md            # Project task list and roadmap
│
README.md
└── 
            
```

### Key Files

- **fshell.cpp**: Implements the main loop and command execution logic for the honeypot. It uses a linked list to manage command tokens and interfaces with the shell parser to simulate shell functionalities.
- **shell_parser.hpp & shell_parser.cpp**: Define and implement the parsing functions and the Node class for command tokens. These files handle tokenizing input, managing command sequences, redirections, and pipes.
- **Makefile**: Automates the build process, compiling all necessary files into the `fshell` executable located in `/usr/bin/fshell`.
- **dashboard/app.py**: Runs the Flask dashboard for monitoring and control.
- **ssh-server/ssh_server.py**: Emulates the SSH server that provides an interactive shell interface to external connections.

## Database structure
 
**Command Usage Log : ```user_commands```** 

| id | connection_id | command   | timestamp           |
|----|---------------|-----------|---------------------|
| 1  | 3             | fastfetch | 2025-02-02 20:25:37 |
| 2  | 3             | ls        | 2025-02-02 20:25:46 |
| 3  | 3             | exit      | 2025-02-02 20:25:48 |

**Connection Log : ```connections```**

| id | ip        | pseudo_id           | duration | status | timestamp           |
|----|-----------|---------------------|----------|--------|---------------------|
| 1  | 127.0.0.1 | 1738517455.8485122  | 0        | 0      | 2025-02-02 18:30:55 |

**IP Geolocations Log : ```ip_geolocations```**

| id | ip         | country | country_code | region | city | lat  | lon  | fetched_at           |
|----|------------|---------|--------------|--------|------|------|------|----------------------|
| 1  | 192.168.1.1| USA     | US           | CA     | SF   | 37.77| -122.42 | 2025-02-02 20:30:00 |

**Login Attempts Log : ```login_attempts```**

| id | ip         | username   | password    | attempt_time           |
|----|------------|------------|-------------|------------------------|
| 1  | 192.168.1.1| admin      | secret123   | 2025-02-02 20:32:00    |

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute this software as per the license terms.

## Contact

For any questions or support, please contact:

- **Frederic MUSIAL**: [frederic.musial@ens.uvsq.fr](mailto:frederic.musial@ens.uvsq.fr)
- **Selyan KABLIA**: [selyan.kablia@ens.uvsq.fr](mailto:selyan.kablia@ens.uvsq.fr)

_Disclaimer: This honeypot is intended for educational and research purposes only. Ensure you comply with all relevant laws and regulations when deploying and using this software._