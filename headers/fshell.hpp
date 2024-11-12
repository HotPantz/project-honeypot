#ifndef FSHELL_HPP
#define FSHELL_HPP

#include <string>
#include <vector>

// Forward declaration of Node
struct Node;

// Global variables
extern Node* head;
extern std::vector<char*> args;
extern std::string command, outputFile, inputFile, errFile;
extern bool run_bg;

// Function declarations
void doexec();
void tokenize2(const char* input, Node*& head);
std::string pop(Node*& head);

#endif // FSHELL_HPP