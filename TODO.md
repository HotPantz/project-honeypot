# Project Honeypot TODO

## Tasks
- [ ] Set up honeypot environment
- [X] Configure logging for command usage
- [ ] Implement connection logging with IP, pseudo ID, duration, time, and date
- [ ] Test honeypot functionality
- [ ] Analyze collected data
- [ ] Create a dashboard for log access and statistics using Flask
- [ ] Simulate common shell commands (e.g., `sudo`) to make the user think they are using a real shell
- [ ] Implement deceptive command responses for common system commands
- [ ] Create a virtual filesystem structure for fake filesystem navigation
- [ ] Simulate sudo behavior with fake permission denied messages
- [ ] Use IP geolocation services for logging attacker’s location
- [ ] Tailor responses based on geolocation data
- [ ] Track and log session duration
- [ ] Log failed command attempts
- [ ] Send real-time notifications for specific command executions
- [ ] Monitor and log brute force and command pattern detection
- [ ] Implement rate limiting for command execution
- [ ] Detect and trap attempts to exit the shell
- [ ] Create honey files for fake file download
- [ ] Add visual analytics to the dashboard
- [ ] Display a real-time command feed on the dashboard
- [ ] Enable customizable alerts for suspicious activity
- [ ] Integrate IP reputation service for highlighting malicious IPs
- [ ] Simulate different user environments based on fake user-agent
- [ ] Track and analyze attacker behavior
- [ ] Display fake vulnerabilities and log exploit attempts
- [ ] Allow different simulated shell environments
- [ ] Simulate restricted access to certain folders and files
- [ ] Populate ps output with decoy processes

## Command Usage Log
| Timestamp           | Command        |
|---------------------|----------------|
| YYYY-MM-DD HH:MM:SS | example_command|

## Connection Log
| Timestamp           | IP Address     | Pseudo ID | Duration |
|---------------------|----------------|-----------|----------|
| YYYY-MM-DD HH:MM:SS | 192.168.1.1    | user123   | 5m       |

## Connection Count Log
| IP Address     | Pseudo ID | Connection Count |
|----------------|-----------|------------------|
| 192.168.1.1    | user123   | 10               |

## Dashboard
- Access to all logs
- Access to real-time logs
- Statistics
- Built using Flask

