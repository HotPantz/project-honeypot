#include "../headers/shell_parser.hpp"
#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <cstring>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>

Node* head = nullptr; // linked list of arguments
std::vector<char*> args;
std::string command, outputFile, inputFile, errFile;
bool run_bg = false; // flag to run in background

void doexec() {
    std::string token;
    int pipefd[2];
    args.push_back(const_cast<char*>(command.c_str()));

    while (head != nullptr) {
        token = pop(head);

        if (token == ">") { // outfile
            outputFile = pop(head);
            continue;
        } else if (token == "<") { // infile
            inputFile = pop(head);
            continue;
        } else if (token == "2>") { // errfile
            errFile = pop(head);
            continue;
        } else if (token == "|") { // pipe
            token = pop(head); // next command

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
                case 0: // execution of the next command
                    head = nullptr;
                    dup2(pipefd[1], STDOUT_FILENO);
                    close(pipefd[0]);
                    close(pipefd[1]);
                    break;
                default: // redirect the output of the command following the | to the input of the first command
                    dup2(pipefd[0], STDIN_FILENO);
                    close(pipefd[0]);
                    close(pipefd[1]);
                    args.clear();
                    command = token;
                    break;
            }
        } else { // simple command + arguments
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

int main(int argc, char* argv[]) {
    std::unique_ptr<char[]> istream(new char[MAX_INPUT_LEN]);
    std::unique_ptr<char[]> cwd(new char[MAX_DIR_LEN]);

    while (true) {
        if (getcwd(cwd.get(), MAX_DIR_LEN) == nullptr) {
            std::cerr << "Couldn't get current working directory" << std::endl;
            std::cout << "\033[1m%\033[0m ";
        } else {
            std::cout << "\033[1m" << cwd.get() << " \033[34m%\033[0m\033[0m ";
        }

        if (fgets(istream.get(), MAX_INPUT_LEN, stdin) == nullptr) {
            return 0;
        }

        char* newline = strchr(istream.get(), '\n');
        if (newline) {
            *newline = '\0';
        }

        tokenize2(istream.get(), head);

        if (head == nullptr) {
            continue;
        } else {
            command = pop(head);
            if (command == "exit") {
                if (head != nullptr) {
                    freeList(head);
                }
                return 0;
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
                    case 0: // execution of the command
                        doexec();
                        break;
                    default: // parent process
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
    return 0;
}
