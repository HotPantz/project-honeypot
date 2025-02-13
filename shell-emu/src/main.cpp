// 12-11-2024 Selyan KABLIA created the main to make the logger, fshell, and shell parser work together

#include "../headers/fshell.hpp"
#include "../headers/shell_parser.hpp"
#include "../headers/logger.hpp"
#include <iostream>
#include <cstring>
#include <memory>
#include <unistd.h>
#include <sys/wait.h>
#include <chrono>

// Ajoutez ces variables globales
auto sessionStart = std::chrono::steady_clock::now();
int commandCount = 0;

int main(int argc, char* argv[]) {
    std::unique_ptr<char[]> istream(new char[MAX_INPUT_LEN]);
    std::unique_ptr<char[]> cwd(new char[MAX_DIR_LEN]);
    std::string publicIP = "";

    publicIP = get_public_ip();
    if(publicIP.empty()) {
        publicIP = "unknown";
    }
    initialize_session_log(publicIP);

    while (true) {
        if (getcwd(cwd.get(), MAX_DIR_LEN) == nullptr) {
            std::cerr << "Couldn't get current working directory" << std::endl;
            std::cout << "\033[1m%\033[0m ";
        } else {
            std::string fullPath(cwd.get());
            size_t pos = fullPath.find_last_of('/');
            std::string baseDir = (pos == std::string::npos) ? fullPath : fullPath.substr(pos + 1);
            std::cout << "\033[1m" << baseDir << "\033[0m $ ";
        }

        if (fgets(istream.get(), MAX_INPUT_LEN, stdin) == nullptr) {
            break;
        }

        char* newline = strchr(istream.get(), '\n');
        if (newline) {
            *newline = '\0';
        }

        log_command(publicIP, istream.get());
        commandCount++; // Incrémentez le compteur de commandes
        tokenize2(std::string(istream.get()), head);

        if (head == nullptr) {
            continue;
        } else {
            command = pop(head);
            if (command == "exit") {
                if (head != nullptr) {
                    freeList(head);
                }
                break;
            } else if (command == "cd") {
                std::string dir = pop(head);
                if (dir.empty()) {
                    std::cerr << "No directory specified" << std::endl;
                } else {
                    if (chdir(dir.c_str()) == -1) {
                        perror("Couldn't change directory - doesn't exist");
                    }
                }
            } else {
                pid_t pid = fork();
                switch (pid) {
                    case -1:
                        perror("Fork error");
                        break;
                    case 0:
                        doexec();
                        break;
                    default:
                        if (!run_bg) {
                            waitpid(pid, nullptr, 0);
                        }
                        run_bg = false;
                        break;
                }
            }
        }
        if (head != nullptr) {
            freeList(head);
        }
    }

    // Calculez la durée de la session
    auto sessionEnd = std::chrono::steady_clock::now();
    int duration = std::chrono::duration_cast<std::chrono::seconds>(sessionEnd - sessionStart).count();

    // Enregistrez le message de déconnexion
    log_disconnection(publicIP, duration, commandCount);

    return 0;
}