#include "../headers/fshell.hpp"
#include "../headers/shell_parser.hpp"
#include "../headers/logger.hpp"
#include <iostream>
#include <cstring>
#include <memory>
#include <cstdlib>
#include <chrono>
#include <cstring>
#include <unistd.h>
#include <sys/wait.h>
#include <pwd.h>

auto sessionStart = std::chrono::steady_clock::now();
int commandCount = 0;

int main(int argc, char* argv[]) {
    std::unique_ptr<char[]> istream(new char[MAX_INPUT_LEN]);
    std::unique_ptr<char[]> cwd(new char[MAX_DIR_LEN]);

    const char* ip_env = std::getenv("SSH_CLIENT_IP");
    std::string publicIP;
    if(ip_env != nullptr && std::strlen(ip_env) > 0) {
        publicIP = std::string(ip_env);
        #ifdef DEBUG
            std::cout << "[DEBUG] SSH_CLIENT_IP: " << publicIP << std::endl;
        #endif
        initialize_session_log(publicIP);
    } 
    else
    {
        #ifdef DEBUG
        std::cout << "[DEBUG] SSH_CLIENT_IP not set, using default." << std::endl;
        #endif
        publicIP = "9.9.9.9";
        initialize_session_log(publicIP);
    }

    // Aller au répertoire home avant de démarrer la boucle du shell
    struct passwd* pw = getpwuid(getuid());
    if (pw != nullptr) {
        const char* homeDir = pw->pw_dir;
        if (chdir(homeDir) != 0) {
            perror("Impossible de changer de répertoire vers HOME");
        }
    } else {
        #ifdef DEBUG
        std::cerr << "Impossible de récupérer le répertoire HOME de l'utilisateur." << std::endl;
        #endif
    }

    while (true) {
        if (getcwd(cwd.get(), MAX_DIR_LEN) == nullptr) {
            std::cerr << "Couldn't get current working directory" << std::endl;
            std::cout << "\033[1m%\033[0m ";
        } else {
            std::string fullPath(cwd.get());
            size_t pos = fullPath.find_last_of('/');
            std::string baseDir = (pos == std::string::npos) ? fullPath : fullPath.substr(pos + 1);

            // Modifier le prompt pour afficher root # si l'utilisateur est froot et dans /froot
            if (std::string(pw->pw_name) == "froot" && fullPath == "/froot") {
                std::cout << "\033[1m" << baseDir << "\033[0m root # ";
            } else if (std::string(pw->pw_name) == "froot") {
                std::cout << "\033[1m" << baseDir << "\033[0m # ";
            } else {
                std::cout << "\033[1m" << baseDir << "\033[0m $ ";
            }
        }

        if (fgets(istream.get(), MAX_INPUT_LEN, stdin) == nullptr) {
            break;
        }

        char* newline = strchr(istream.get(), '\n');
        if (newline) {
            *newline = '\0';
        }

        log_command(publicIP, istream.get());
        commandCount++;
        tokenize2(std::string(istream.get()), head);

        if(head == nullptr){
            continue;
        } 
        else{
            command = pop(head);
            if(command == "exit") 
            {
                if(head != nullptr){
                    freeList(head);
                }
                break;
            } 
            else if (command == "cd") {
                std::string dir = pop(head);
                if (dir.empty()) {
                    // no target dir, move to home
                    struct passwd* pw = getpwuid(getuid());
                    if (pw != nullptr) {
                        dir = std::string(pw->pw_dir);
                    } else {
                        #ifdef DEBUG
                        std::cerr << "Impossible de récupérer le répertoire HOME de l'utilisateur." << std::endl;
                        #endif
                        continue;
                    }
                }
                // try changing directory as given
                if (chdir(dir.c_str()) == -1) {
                    // if it fails and it doesn't appear to be an absolute or already relative
                    if (dir.front() != '/' && dir.substr(0, 2) != "./" && dir.substr(0, 3) != "../") {
                        std::string prefixedDir = "./" + dir;
                        if (chdir(prefixedDir.c_str()) == -1) {
                            perror("Couldn't change directory");
                        }
                    } else {
                        perror("Couldn't change directory");
                    }
                }
            }
            else if (command == "whoami") {
                // Modifier la commande whoami pour afficher root si l'utilisateur est froot
                if (std::string(pw->pw_name) == "froot") {
                    std::cout << "root" << std::endl;
                } else {
                    std::cout << pw->pw_name << std::endl;
                }
            }
            else
            {
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

    //session duration
    auto sessionEnd = std::chrono::steady_clock::now();
    int duration = std::chrono::duration_cast<std::chrono::seconds>(sessionEnd - sessionStart).count();

    //disconnect message push to the log
    log_disconnection(publicIP, duration, commandCount);

    return 0;
}