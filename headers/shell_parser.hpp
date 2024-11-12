#ifndef SHELL_PARSER_HPP
#define SHELL_PARSER_HPP

#include <string>
#include <list>

constexpr int MAX_ARGS = 51; // 50 arguments + NULL
constexpr int MAX_TOKEN_LEN = 4097; // 4096 + '\0'
constexpr int MAX_INPUT_LEN = 8192;
constexpr int MAX_DIR_LEN = 4097;

class Node {
public:
    std::string token;
    Node* next;

    Node(const std::string& token) : token(token), next(nullptr) {}
};

/*  Splits the input into tokens (if separated by spaces) 
    and creates a linked list containing them */ 
void tokenize(const std::string& istream, Node*& head);

/*  Splits the input into tokens like tokenize but takes
    quotes into account: ' ' and " " */
void tokenize2(const std::string& istream, Node*& head);

/*  Removes leading spaces before the command */
std::string removeLeadingSpaces(const std::string& str);

/* Retrieves the first token from the list and removes it */
std::string pop(Node*& head);

/* Adds a token to the end of the list */
void enqueue(Node*& head, const std::string& token);

/* Frees the memory of all nodes in the list */
void freeList(Node*& head);

/*  Retrieves the n-th token in the list
    If n > number of tokens: returns an empty string, otherwise returns the token */
std::string getNthToken(Node* head, int n);

/* Prints the list of tokens (used for debugging) */
void printList(Node* head);

/* Creates a list node containing the token */
Node* createNode(const std::string& token);

#endif // SHELL_PARSER_HPP
