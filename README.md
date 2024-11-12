# Project Honeypot

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
- **Command Logging**: Records all executed commands into a log file for detailed analysis of attacker activities.
- **Mini File System**: Implements a simplified file system structure, including support for the `wget` command.
- **User and Group Simulation**: Features commands like `whoami` to enhance the realism of the simulated environment.
- **Security Measures**: Designed to run within a virtual machine to ensure the host system remains protected from potential threats.

## File Structure

The project is organized as follows:

```
.
├── fshell             # Executable file after build
├── headers
│   └── shell_parser.hpp   # Header file for parsing shell input and managing command nodes
├── Makefile           # Build file for easy compilation
├── README.md          # Documentation for the project
└── src
    ├── fshell.cpp         # Main program file that runs the simulated shell
    └── shell_parser.cpp   # Source file for parsing shell commands and handling input tokens
```

### Key Files

- **fshell.cpp**: Implements the main loop and command execution logic for the honeypot. It uses a linked list to manage command tokens and interacts with the shell_parser module to handle various shell functionalities.
- **shell_parser.hpp & shell_parser.cpp**: Define and implement the Node class and parsing functions for command tokens. `shell_parser.cpp` provides utilities for tokenizing commands, handling redirections and pipes, and simulating command execution.
- **Makefile**: Automates the build process, compiling all necessary files into the `fshell` executable.

## Installation

### Prerequisites

- **C++ Compiler**: Ensure you have a C++ compiler installed (e.g., `g++`).
- **CMake**: Required for building the project.
- **Virtualization Software**: Tools like VirtualBox or VMware to set up a secure virtual environment.

### Steps

1. **Clone the Repository**

    ```bash
    git clone https://github.com/HotPantz/project-honeypot.git
    cd project-honeypot
    ```

2. **Build the Project**

    ```bash
    make
    ```

3. **Set Up the Virtual Environment**
    - Install and configure your preferred virtualization software.
    - Create a new virtual machine and ensure it is isolated from your host network.
    - Deploy the honeypot within the virtual machine to maintain host security.

## Usage

1. **Run the Honeypot**

    Execute the honeypot program from the main directory:

    ```bash
    ./fshell
    ```

2. **Configure Network Settings**
    - Forward the SSH port (default is 22) from your router to the IP address of the virtual machine running the honeypot.
    - Ensure that the honeypot is accessible from the internet to attract potential attackers.

3. **Monitor Activity**
    - All commands executed by attackers are logged in the `commands.log` file located in the project directory.
    - Analyze the log file to understand attacker behaviors and strategies.

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

