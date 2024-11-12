#include "../headers/fshell.hpp"
#include "../headers/shell_parser.hpp"
#include <iostream>
#include <cstring>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>

// Global variables
Node* head = nullptr;
std::vector<char*> args;
std::string command, outputFile, inputFile, errFile;
bool run_bg = false;

// Function to execute commands
void doexec() {
    std::string token;
    int pipefd[2];
    args.push_back(const_cast<char*>(command.c_str()));

    while (head != nullptr) {
        token = pop(head);

        if (token == ">") {
            outputFile = pop(head);
            continue;
        } else if (token == "<") {
            inputFile = pop(head);
            continue;
        } else if (token == "2>") {
            errFile = pop(head);
            continue;
        } else if (token == "|") {
            token = pop(head);

            if (token.empty() || head == nullptr) {
                std::cerr << "No command after pipe" << std::endl;
                exit(EXIT_FAILURE);
            }

            pipe(pipefd);
            pid_t pid = fork();
            switch (pid) {
                case -1:
                    perror("Fork error");
                    break;
                case 0:
                    head = nullptr;
                    dup2(pipefd[1], STDOUT_FILENO);
                    close(pipefd[0]);
                    close(pipefd[1]);
                    break;
                default:
                    dup2(pipefd[0], STDIN_FILENO);
                    close(pipefd[0]);
                    close(pipefd[1]);
                    args.clear();
                    command = token;
                    break;
            }
        } else {
            char* arg = new char[token.size() + 1];
            std::strcpy(arg, token.c_str());
            args.push_back(arg);
        }
    }

    if (args.size() < MAX_ARGS) {
        args.push_back(nullptr);
    } else {
        std::cerr << "Too many arguments" << std::endl;
        exit(EXIT_FAILURE);
    }

    if (!outputFile.empty()) {
        int fd = open(outputFile.c_str(), O_WRONLY | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR);
        if (fd == -1) {
            perror("Couldn't open output file");
            exit(EXIT_FAILURE);
        }
        if (dup2(fd, STDOUT_FILENO) == -1) {
            perror("Couldn't duplicate file descriptor");
            exit(EXIT_FAILURE);
        }
        close(fd);
    }

    if (!inputFile.empty()) {
        int fd = open(inputFile.c_str(), O_RDONLY);
        if (fd == -1) {
            perror("Couldn't open input file");
            exit(EXIT_FAILURE);
        }
        if (dup2(fd, STDIN_FILENO) == -1) {
            perror("Couldn't duplicate file descriptor");
            exit(EXIT_FAILURE);
        }
        close(fd);
    }

    if (!errFile.empty()) {
        int fd = open(errFile.c_str(), O_WRONLY | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR);
        if (fd == -1) {
            perror("Couldn't open error file");
            exit(EXIT_FAILURE);
        }
        if (dup2(fd, STDERR_FILENO) == -1) {
            perror("Couldn't duplicate file descriptor");
            exit(EXIT_FAILURE);
        }
        close(fd);
    }

    execvp(command.c_str(), args.data());
    std::cerr << "Couldn't execute " << command << std::endl;
    exit(EXIT_FAILURE);
}