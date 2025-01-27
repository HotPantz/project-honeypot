// 12-11-2024 Selyan KABLIA Created the file, Added function declarations for logging and IP pseudonym generation
#ifndef LOGGER_HPP
#define LOGGER_HPP

#include <string>

// Structure to store IP information with pseudonym and ID
struct IPInfo {
    std::string id;
    std::string pseudonym;
};

// Initializes the logging session, creating a log file with a timestamped name
void initialize_log();

// Logs a command along with a timestamp
void log_command(const std::string& command);

// Saves and closes the log file upon program exit
void close_log();

// Retrieves the public IP address of the user
std::string get_user_ip();

// Generates or retrieves a pseudonym and ID based on the user's IP
IPInfo get_pseudonym(const std::string& ip);  // Only one declaration

#endif // LOGGER_HPP
