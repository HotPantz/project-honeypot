# Project Honeypot TODO

## Tasks
- [x] Set up honeypot environment 
- [x] Configure logging for command usage 
- [x] Implement connection logging with IP, pseudo ID, duration, time, and date 
- [x] Test honeypot functionality
- [x] Add Authentification methods for SSH server
- [x] Create a DB table to log the login credentials in order to see the most common ones 
- [x] Write "User (IP) disconnected " in the live shell output upon disconnect of a user 
- [x] Differentiate between live (active) connections and ones that are closed (IMPORTANT) - find a method to check if it's active
- [x] Only allow the selection of ACTIVE connections in the live output
- [x] Display various stats on the dashboard like most popular commands, average session duration etc
- [x] Create a dashboard for log access and statistics using Flask
- [x] FIX cd in the shell so that "cd <directory>" works without "./<directory>"
- [x] Create a list of commands that are allowed to be executed by the user (list loaded in main.cpp)
- [x] Populate ps output with decoy processes
- [x] Simulate common shell commands (e.g., `sudo`) to make the user think they are using a real shell
- [x] Implement deceptive command responses for common system commands
- [ ] Don't allow user to exit the fake file system
- [ ] Simulate sudo behavior with fake permission denied messages
- [x] Use IP geolocation services for logging attacker's location 
- [x] Track and log session duration 
- [x] Log failed command attempts 
- [ ] Create honey files for fake file download
- [x] Add visual analytics to the dashboard 
- [x] Display a real-time command feed on the dashboard 

TOTAL COMPLETED : 21 / 24

