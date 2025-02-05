// 12-11-2024 Selyan KABLIA Created the file, Added function declarations for logging and IP pseudonym generation
// 7-12-2024 Frederic MUSIAL Added the function definitions for logging and IP pseudonym generation
#ifndef LOGGER_HPP
#define LOGGER_HPP

#include <string>

// Writes an error message to the session's log file in order not to send it to the user's terminal
void write_error_to_log(const std::string& errMsg);

// Initializes the logging session, creating a log file with a timestamped name
void initialize_session_log(const std::string& publicIP);

// Logs a command along with a timestamp & IP
void log_command(const std::string& publicIP, const std::string& command);

// Saves and closes the log file upon program exit
void close_log();

// Retrieves the public IP address of the user
std::string get_public_ip();

#endif // LOGGER_HPP
