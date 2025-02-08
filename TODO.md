# Project Honeypot TODO

## Tasks
- [x] Set up honeypot environment
- [x] Configure logging for command usage
- [x] Implement connection logging with IP, pseudo ID, duration, time, and date
- [x] Test honeypot functionality
- [ ] Write "User (IP) disconnected " in the live shell output upon disconnect of a user
- [ ] Create a DB table to log the login credentials in order to see the most common ones
- [ ] Display various stats on the dashboard like most popular commands, average session duration etc
- [x] Create a dashboard for log access and statistics using Flask
- [ ] Simulate common shell commands (e.g., `sudo`) to make the user think they are using a real shell
- [ ] Implement deceptive command responses for common system commands
- [ ] Create a virtual filesystem structure for fake filesystem navigation
- [ ] Simulate sudo behavior with fake permission denied messages
- [x] Use IP geolocation services for logging attacker’s location
- [x] Track and log session duration
- [x] Log failed command attempts
- [ ] Send real-time notifications for specific command executions
- [ ] Monitor and log brute force and command pattern detection
- [ ] Implement rate limiting for command execution
- [ ] Detect and trap attempts to exit the shell
- [ ] Create honey files for fake file download
- [x] Add visual analytics to the dashboard
- [x] Display a real-time command feed on the dashboard
- [ ] Enable customizable alerts for suspicious activity
- [ ] Integrate IP reputation service for highlighting malicious IPs
- [ ] Simulate different user environments based on fake user-agent
- [ ] Display fake vulnerabilities and log exploit attempts
- [ ] Simulate restricted access to certain folders and files
- [ ] Populate ps output with decoy processes

TOTAL COMPLETED : 10 / 28

## Command Usage Log : user_commands

| id | connection_id | command   | timestamp           |
|----|---------------|-----------|---------------------|
| 1  | 3             | fastfetch | 2025-02-02 20:25:37 |
| 2  | 3             | ls        | 2025-02-02 20:25:46 |
| 3  | 3             | exit      | 2025-02-02 20:25:48 |

## Connection Log : connections

| id | ip        | pseudo_id           | duration | timestamp           |
|----|-----------|---------------------|----------|---------------------|
| 1  | 127.0.0.1 | 1738517455.8485122  | 0        | 2025-02-02 18:30:55 |


