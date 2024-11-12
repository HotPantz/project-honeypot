# Project Honeypot TODO

## Tasks
- [ ] Set up honeypot environment
- [X] Configure logging for command usage
- [ ] Implement connection logging with IP, pseudo ID, duration, time, and date
- [ ] Test honeypot functionality
- [ ] Analyze collected data
- [ ] Create a dashboard for log access and statistics using Flask

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

