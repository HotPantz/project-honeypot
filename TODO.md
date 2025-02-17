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
- [ ] Simulate restricted access to certain folders and files
- [ ] Populate ps output with decoy processes
- [ ] Simulate common shell commands (e.g., `sudo`) to make the user think they are using a real shell
- [ ] Implement deceptive command responses for common system commands
- [ ] Create a virtual filesystem structure for fake filesystem navigation
- [ ] Don't allow user to exit the fake file system
- [ ] Simulate sudo behavior with fake permission denied messages
- [x] Use IP geolocation services for logging attacker's location 
- [x] Track and log session duration 
- [x] Log failed command attempts 
- [ ] Detect and trap attempts to exit the shell
- [ ] Create honey files for fake file download
- [x] Add visual analytics to the dashboard 
- [x] Display a real-time command feed on the dashboard 

TOTAL COMPLETED : 14 / 25

