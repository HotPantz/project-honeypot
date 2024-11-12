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



// Global variables
Node* head = nullptr; // linked list of arguments
std::vector<char*> args; // vector to store command arguments
std::string command, outputFile, inputFile, errFile; // strings to store command, output file, input file, and error file
bool run_bg = false; // flag to run in background

// Function to execute commands
/**
 * @brief Executes a command with optional input/output/error redirection and piping.
 *
 * This function processes a linked list of command arguments, handling special tokens
 * for input redirection ("<"), output redirection (">"), error redirection ("2>"), and
 * piping ("|"). It sets up the necessary file descriptors and forks processes as needed
 * to execute the command with the specified redirections and piping.
 *
 * The function performs the following steps:
 * 1. Processes the linked list of arguments to handle special tokens.
 * 2. Sets up pipes and forks processes for commands separated by pipes.
 * 3. Handles input, output, and error redirection by duplicating file descriptors.
 * 4. Executes the command using execvp.
 *
 * @note The function assumes that the linked list of arguments (head) and the command
 *       string (command) are properly initialized before calling this function.
 * @note The function exits with an error message if any system call fails.
 *
 * @param None
 * @return None
 */
void doexec() {
    std::string token;
    int pipefd[2]; // file descriptors for pipe
    args.push_back(const_cast<char*>(command.c_str())); // add command to args

    // Process the linked list of arguments
    while (head != nullptr) {
        token = pop(head); // get the next token

        if (token == ">") { // output redirection
            outputFile = pop(head);
            continue;
        } else if (token == "<") { // input redirection
            inputFile = pop(head);
            continue;
        } else if (token == "2>") { // error redirection
            errFile = pop(head);
            continue;
        } else if (token == "|") { // pipe
            token = pop(head); // next command

            if (token.empty() || head == nullptr) {
                std::cerr << "No command after pipe" << std::endl;
                exit(EXIT_FAILURE);
            }

            pipe(pipefd); // create pipe
            pid_t pid = fork(); // fork process
            switch (pid) {
                case -1:
                    perror("Fork error");
                    break;
                case 0: // child process
                    head = nullptr;
                    dup2(pipefd[1], STDOUT_FILENO); // redirect stdout to pipe
                    close(pipefd[0]);
                    close(pipefd[1]);
                    break;
                default: // parent process
                    dup2(pipefd[0], STDIN_FILENO); // redirect stdin to pipe
                    close(pipefd[0]);
                    close(pipefd[1]);
                    args.clear(); // clear args for next command
                    command = token; // set command to next command
                    break;
            }
        } else { // simple command + arguments
            char* arg = new char[token.size() + 1];
            std::strcpy(arg, token.c_str());
            args.push_back(arg); // add argument to args
        }
    }

    if (args.size() < MAX_ARGS) {
        args.push_back(nullptr); // null-terminate args
    } else {
        std::cerr << "Too many arguments" << std::endl;
        exit(EXIT_FAILURE);
    }

    // Handle output redirection
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

    // Handle input redirection
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

    // Handle error redirection
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

    // Execute the command
    execvp(command.c_str(), args.data());
    std::cerr << "Couldn't execute " << command << std::endl;
    exit(EXIT_FAILURE);
}

int main(int argc, char* argv[]) {
    std::unique_ptr<char[]> istream(new char[MAX_INPUT_LEN]); // input stream buffer
    std::unique_ptr<char[]> cwd(new char[MAX_DIR_LEN]); // current working directory buffer

    while (true) {
        // Print the current working directory
        if (getcwd(cwd.get(), MAX_DIR_LEN) == nullptr) {
            std::cerr << "Couldn't get current working directory" << std::endl;
            std::cout << "\033[1m%\033[0m ";
        } else {
            std::cout << "\033[1m" << cwd.get() << " \033[34m%\033[0m\033[0m ";
        }

        // Read input from the user
        if (fgets(istream.get(), MAX_INPUT_LEN, stdin) == nullptr) {
            return 0;
        }

        // Remove newline character from input
        char* newline = strchr(istream.get(), '\n');
        if (newline) {
            *newline = '\0';
        }

        // Tokenize the input
        tokenize2(istream.get(), head);

        if (head == nullptr) {
            continue; // no input
        } else {
            command = pop(head); // get the command
            if (command == "exit") {
                if (head != nullptr) {
                    freeList(head); // free the linked list
                }
                return 0;
            } else if (command == "cd") {
                std::string dir = pop(head); // get the directory
                if (dir.empty()) {
                    std::cerr << "No directory specified" << std::endl;
                } else {
                    if (chdir(dir.c_str()) == -1) {
                        perror("Couldn't change directory - doesn't exist");
                    }
                }
            } else {
                pid_t pid = fork(); // fork process
                switch (pid) {
                    case -1:
                        perror("Fork error");
                        break;
                    case 0: // child process
                        doexec(); // execute the command
                        break;
                    default: // parent process
                        if (!run_bg) {
                            waitpid(pid, nullptr, 0); // wait for child process to finish
                        }
                        run_bg = false; // reset background flag
                        break;
                }
            }
        }
        if (head != nullptr) {
            freeList(head); // free the linked list
        }
    }
    return 0;
}
