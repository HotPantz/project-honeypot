// 12-11-2024 Selyan KABLIA created this file to log commands, date, IP, and pseudonym with generated pseudonym for each IP

#include "../headers/logger.hpp"
#include <curl/curl.h>  // Required for libcurl
#include <fstream>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <sys/stat.h>
#include <sys/types.h>
#include <unordered_map>
#include <random>
#include <arpa/inet.h>
#include <ifaddrs.h>

// Global file stream for the log file
std::ofstream logFile;

// Map to store IP to pseudonym and ID mappings
std::unordered_map<std::string, IPInfo> ipToInfoMap;

// Expanded lists of adjectives and nouns for pseudonym generation
const std::vector<std::string> adjectives = {
    "Velvety", "Protactinium", "Ali", "Lean", "Excellent", "Happy", "Lively", "Wide-eyed", "Hydra", "Handy",
    "Brave", "Mellow", "Sunny", "Silent", "Swift", "Mighty", "Wise", "Curious", "Gentle", "Fierce",
    "Brilliant", "Witty", "Clever", "Noble", "Vivid", "Playful", "Nimble", "Bold", "Calm", "Mystic",
    "Dynamic", "Gracious", "Eager", "Jolly", "Radiant", "Savvy", "Lucky", "Majestic", "Luminous", "Sparkling",
    "Daring", "Gallant", "Cheerful", "Joyful", "Blissful", "Graceful", "Kind", "Fearless", "Gallant", "Noble",
    "Charming", "Sturdy", "Proud", "Gentle", "Sly", "Cunning", "Serene", "Vigilant", "Humble", "Diligent"
};

const std::vector<std::string> nouns = {
    "Closs", "Dimos", "Bulldog", "Terrier", "Bearmode", "Kale", "Nikaila", "Otter", "Dragon", "Falcon",
    "Phoenix", "Panda", "Wolf", "Tiger", "Hawk", "Lion", "Panther", "Rhino", "Bear", "Fox",
    "Badger", "Eagle", "Viper", "Stag", "Serpent", "Lynx", "Griffin", "Mantis", "Leopard", "Cougar",
    "Jaguar", "Raven", "Scorpion", "Unicorn", "Thunder", "Storm", "Ghost", "Shadow", "Vortex", "Tempest",
    "Flame", "Spark", "Rocket", "Cyclone", "Comet", "Meteor", "Avalanche", "Blade", "Frost", "Blizzard",
    "Whale", "Mammoth", "Bison", "Lizard", "Tigerfish", "Moose", "Phoenix", "Wolverine", "Jackal", "Cobra"
};

// Callback function for libcurl to write data into a string
static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

// Retrieves the public IP address using libcurl
std::string get_public_ip() {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    curl = curl_easy_init();
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, "https://api.ipify.org");
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        res = curl_easy_perform(curl);
        if(res != CURLE_OK) {
            std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
        }
        curl_easy_cleanup(curl);
    }
    return readBuffer;
}

// Helper to generate a unique ID for each IP
std::string generate_unique_id() {
    static int counter = 1;
    return "ID" + std::to_string(counter++);
}

// Helper function to generate a meaningful pseudonym
std::string generate_random_pseudonym() {
    static std::mt19937 rng(std::random_device{}());
    std::uniform_int_distribution<> adjDist(0, adjectives.size() - 1);
    std::uniform_int_distribution<> nounDist(0, nouns.size() - 1);

    return adjectives[adjDist(rng)] + nouns[nounDist(rng)];
}

// Retrieves or assigns a pseudonym and ID based on IP
IPInfo get_pseudonym(const std::string& ip) {
    static const std::string pseudoFile = "../pseudonyms.txt";
    std::ifstream infile(pseudoFile);
    std::ofstream outfile;

    // Load existing pseudonyms
    std::string line;
    while (std::getline(infile, line)) {
        std::istringstream iss(line);
        std::string existingIp, existingId, existingPseudo;
        if (iss >> existingIp >> existingId >> existingPseudo) {
            ipToInfoMap[existingIp] = {existingId, existingPseudo};
        }
    }
    infile.close();

    // Check if IP already has a pseudonym and ID
    if (ipToInfoMap.find(ip) != ipToInfoMap.end()) {
        return ipToInfoMap[ip];
    }

    // Generate and save a new pseudonym and ID
    std::string id = generate_unique_id();
    std::string pseudo = generate_random_pseudonym();
    ipToInfoMap[ip] = {id, pseudo};

    outfile.open(pseudoFile, std::ios::app);
    if (outfile.is_open()) {
        outfile << ip << " " << id << " " << pseudo << std::endl;
        outfile.close();
    }
    return {id, pseudo};
}

// Initializes the log file with a timestamped name
void initialize_log() {
    std::string logDir = "../logs";
    struct stat info;
    if (stat(logDir.c_str(), &info) != 0) {
        if (mkdir(logDir.c_str(), 0777) != 0) {
            std::cerr << "Couldn't create log directory" << std::endl;
            return;
        }
    }

    std::time_t now = std::time(nullptr);
    std::tm* localDate = std::localtime(&now);
    std::ostringstream oss;
    oss << logDir << "/shell_log_" << std::put_time(localDate, "%Y-%m-%d_%H-%M-%S") << ".txt";
    std::string logFilePath = oss.str();

    logFile.open(logFilePath, std::ios::app);
    if (!logFile.is_open()) {
        std::cerr << "Couldn't open log file" << std::endl;
    }

    // Get the public IP, pseudonym, and ID for logging session info
    std::string userIp = get_public_ip();  // Updated to use the public IP function
    IPInfo ipInfo = get_pseudonym(userIp);
    logFile << "IP: " << userIp << "\nPseudonym: " << ipInfo.pseudonym << "\nID: " << ipInfo.id << "\n\n";
}

// Logs a command with timestamp
void log_command(const std::string& command) {
    if (logFile.is_open()) {
        std::time_t now = std::time(nullptr);
        std::tm* localDate = std::localtime(&now);

        logFile << "[" << std::put_time(localDate, "%Y-%m-%d %H:%M:%S") << "] - Command: " << command << std::endl;
    }
}

// Closes the log file upon exit
void close_log() {
    if (logFile.is_open()) {
        logFile.close();
    }
}

// Ensure the log is saved when the program exits
struct LogSaver {
    ~LogSaver() {
        close_log();
    }
} logSaver;
