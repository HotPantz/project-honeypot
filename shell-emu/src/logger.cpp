#include "../headers/logger.hpp"
#include <curl/curl.h>
#include <fstream>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <sys/stat.h>
#include <sys/types.h>
#include <string>
#include <stdexcept>
#include <cstdio>
#include <cstring>
#include <cerrno>
#include <cstring>
#include <unistd.h>  // for getuid()

std::ofstream sessionLogFile;
std::string sessionLogFilePath;


//Callback function for libcurl to write data into a string
static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) 
{
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

void write_error_to_log(const std::string& errMsg) 
{
    if(sessionLogFile.is_open()) 
    {
        std::time_t now = std::time(nullptr);
        std::tm* localDate = std::localtime(&now);
        std::ostringstream oss;
        oss << "[" << std::put_time(localDate, "%Y-%m-%d %H:%M:%S") 
            << "] [ERROR] " << errMsg << "\n";
        sessionLogFile << oss.str();
        sessionLogFile.flush();
    }
}

//deprecated
std::string get_public_ip() 
{
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if(curl) 
    {
        curl_easy_setopt(curl, CURLOPT_URL, "https://api.ipify.org");
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        res = curl_easy_perform(curl);
        if(res != CURLE_OK) 
        { //not using the write_error_to_log since we get the IP before initializing the log
            std::stringstream errstream;
            errstream << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
            readBuffer = errstream.str();
        }
        curl_easy_cleanup(curl);
    }
    return readBuffer;
}

// Initializes a unique log file for the session
void initialize_session_log(const std::string& publicIP)
{
     
    //reading LOG_DIR env var from "../../.env"
     std::string logDir;
     const char* env_log_dir = std::getenv("LOG_DIR");
     if(env_log_dir != nullptr)
     {
         logDir = std::string(env_log_dir);
     } 
     else
     {
         logDir = "/var/log/analytics";
     }
     if (logDir.back() != '/')
         logDir.push_back('/');
    
    #ifdef DEBUG
    std::cerr << "[DEBUG] Trying log directory: " << logDir << std::endl;
    std::cerr << "[DEBUG] Effective UID: " << getuid() << std::endl;
    #endif
    
    struct stat info;
    if(stat(logDir.c_str(), &info) != 0)
    {
        if (mkdir(logDir.c_str(), 0777) != 0)
        {
            #ifdef DEBUG
            std::cerr << "[DEBUG] mkdir failed for " << logDir << ". Error: " 
                      << std::strerror(errno) << std::endl;
            #endif
            return;
        }
        else
        {
            #ifdef DEBUG
            std::cerr << "[DEBUG] Successfully created " << logDir << std::endl;
            #endif
        }
    } 
    else{
        if(!S_ISDIR(info.st_mode))
        {
            #ifdef DEBUG
            std::cerr << "[DEBUG] " << logDir << " exists but is not a directory." << std::endl;
            #endif
            return;
        }
        else
        {
            #ifdef DEBUG
            std::cerr << "[DEBUG] Log directory " << logDir << " exists." << std::endl;
            #endif
        }
    }
    
    std::time_t now = std::time(nullptr);
    std::tm* localDate = std::localtime(&now);
    std::ostringstream oss;
    oss << logDir << "session_" << publicIP << "_" 
        << std::put_time(localDate, "%Y-%m-%d_%H-%M-%S") << ".txt";
    sessionLogFilePath = oss.str();
    
    std::cerr << "[DEBUG] Constructed session log file path: " << sessionLogFilePath << std::endl;
    
    //Temporarily set umask to 0022 so that the file is created with 0644 permissions
    mode_t old_mask = umask(0022);
    sessionLogFile.open(sessionLogFilePath, std::ios::app);
    umask(old_mask);
    
    if(!sessionLogFile.is_open()){
        #ifdef DEBUG
        std::cerr << "[DEBUG] Failed to open session log file: " << sessionLogFilePath 
                  << ". Error: " << std::strerror(errno) << std::endl;
        #endif
        return;
    }
    else
    {
        #ifdef DEBUG
        std::cerr << "[DEBUG] Successfully opened session log file: " << sessionLogFilePath << std::endl;
        #endif
    }
    
    if(chmod(sessionLogFilePath.c_str(), 0644) != 0)
    {
        #ifdef DEBUG
        std::cerr << "[DEBUG] Failed to chmod session log file: " << sessionLogFilePath 
                  << ". Error: " << std::strerror(errno) << std::endl;
        #endif
    }
}

// Logs a command for the session in a csv manner, with timestamp and user IP)
void log_command(const std::string& userIp, const std::string& command)
{
    if(sessionLogFile.is_open())
    {
        std::time_t now = std::time(nullptr);
        std::tm* localDate = std::localtime(&now);
        std::ostringstream oss;
        oss << std::put_time(localDate, "%Y-%m-%d %H:%M:%S") << "," << userIp << "," << command << "\n";
        sessionLogFile << oss.str();
        sessionLogFile.flush();
    }
}


// Logs the disconnection message
void log_disconnection(const std::string& userIp, int duration, int commandCount) {
    if(sessionLogFile.is_open()) {
        std::ostringstream oss;
        oss << "User " << userIp << " disconnected after " << duration << "s (" << commandCount << " cmds).\n";
        sessionLogFile << oss.str();
        sessionLogFile.flush();
    }
}


// Closes the session log file 
void close_session_log() {
    if (sessionLogFile.is_open()) {
        sessionLogFile.close();
    }
}


// Ensure the session log is closed on exit
struct LogSaver {
    ~LogSaver() {
        close_session_log();
    }
} logSaver;