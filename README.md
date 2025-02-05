# Project Honeypot

## Overview

**Project Honeypot** is a C++-based SSH honeypot designed to simulate an accessible shell, attracting and logging malicious attack attempts. The primary objective is to analyze attacker behavior while ensuring the security of the host system.

## Table of Contents

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

## File Structure

The project is organized as follows:

```
.
├── .env                  # Environment configuration file
├── .gitignore            # Git ignore rules
├── dashboard             # Flask dashboard for visualization and control
│   ├── app.py            # Main Flask application
│   ├── static/           # Static assets for the dashboard
│   ├── templates/        # HTML templates for the dashboard
│   └── venv/             # Virtual environment for Python dependencies
├── data/                 # Data files used by the project
├── logs/                 # Directory containing shell command log files
│   ├── shell_log_2024-11-12_16-04-23.txt
│   ├── shell_log_2025-02-02_19-21-44.txt
│   └── ...               # Additional log files
├── 

mariadb_setup.sh

      # Script to set up the MariaDB database
├── 

mariadb_tables.txt

    # SQL commands for database tables
├── 

pseudonyms.txt

        # List of pseudonyms for simulated users
├── 

README.md

             # Project documentation
├── shell-emu             # Honeypot emulator directory
│   ├── bin/              # Contains the `fshell` executable after build
│   ├── headers/          # Header files (e.g., for shell parsing)
│   └── ...               # Additional source files and assets
├── ssh-server            # SSH server simulation files
│   └── ssh_server.py     # Python script for the SSH server
├── 

ssh_user_setup.sh

     # Script for setting up simulated SSH users
└── 

TODO.md

               # Project to-do list and roadmap
```

### Key Files

- **fshell.cpp**: Implements the main loop and command execution logic for the honeypot. It uses a linked list to manage command tokens and interfaces with the shell parser to simulate shell functionalities.
- **shell_parser.hpp & shell_parser.cpp**: Define and implement the parsing functions and the Node class for command tokens. These files handle tokenizing input, managing command sequences, redirections, and pipes.
- **Makefile**: Automates the build process, compiling all necessary files into the `fshell` executable located in `shell-emu/bin/`.
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

| id | ip        | pseudo_id           | duration | timestamp           |
|----|-----------|---------------------|----------|---------------------|
| 1  | 127.0.0.1 | 1738517455.8485122  | 0        | 2025-02-02 18:30:55 |

## Installation

### Prerequisites

- **C++ Compiler**: Ensure you have a C++ compiler installed (e.g., `g++`).
- **CMake**: Required for building the project.
- **Python & Dependencies**: Install the required Python packages:
  
  ```bash
  pip install flask flask-socketio paramiko pymysql python-dotenv requests watchdog
  ```

### Steps

1. **Clone the Repository**

    ```bash
    git clone https://github.com/HotPantz/project-honeypot.git
    cd project-honeypot
    ```

2. **Build the Project**

    Navigate to the shell-emu directory and run:

    ```bash
    make
    ```

3. **Set Up the Virtual Environment**
    - Install and configure your preferred virtualization software.
    - Create a new virtual machine and ensure it is isolated from your host network.
    - Deploy the honeypot within the virtual machine to maintain host security.

## Usage

1. **Run the Honeypot Shell**

    Execute the honeypot CLI (located in bin):

    ```bash
    ./shell-emu/bin/fshell
    ```

2. **Start the SSH Server**

    Run the SSH server to simulate incoming SSH connections:

    ```bash
    python ssh-server/ssh_server.py
    ```

3. **Launch the Dashboard**

    Start the Flask dashboard by navigating to the dashboard directory and running:

    ```bash
    python dashboard/app.py
    ```

4. **Monitor Activity**

    - All command logs generated by the honeypot are saved in the logs directory.
    - Analyze these log files to understand attacker behaviors and strategies.

5. **Configure Network Settings**

    - Forward the SSH port (default is 22) from your router to the IP address of the virtual machine running the honeypot.
    - Ensure that the honeypot is accessible from the internet to attract potential attackers.

## Contributing

Contributions are welcome! If you have suggestions for improvements or want to report a bug, please open an issue or submit a pull request.

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes with clear messages.
4. Push to your fork and submit a pull request.

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute this software as per the license terms.

## Contact

For any questions or support, please contact:

- **Frederic MUSIAL**: [frederic.musial@ens.uvsq.fr](mailto:frederic.musial@ens.uvsq.fr)
- **Selyan KABLIA**: [selyan.kablia@ens.uvsq.fr](mailto:selyan.kablia@ens.uvsq.fr)

_Disclaimer: This honeypot is intended for educational and research purposes only. Ensure you comply with all relevant laws and regulations when deploying and using this software._