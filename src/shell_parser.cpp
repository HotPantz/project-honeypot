#include "../headers/shell_parser.hpp"
#include <string>
#include <iostream>
#include <cctype>

extern int run_bg;

// Function to create a new node with the given token
/**
 * @brief Creates a new node with the given token.
 *
 * This function allocates memory for a new node and initializes it with the provided token.
 *
 * @param token The token to be stored in the new node.
 * @return A pointer to the newly created node.
 */
Node* createNode(const std::string& token) {
    return new Node(token);
}

// Function to add a new node with the given token to the end of the list
/**
 * @brief Adds a new node with the given token to the end of the list.
 *
 * This function creates a new node with the provided token and appends it to the end of the linked list.
 *
 * @param head A reference to the head pointer of the linked list.
 * @param token The token to be added to the list.
 */
void enqueue(Node*& head, const std::string& token) {
    Node* newNode = createNode(token);
    if (!head) {
        head = newNode;
    } else {
        Node* current = head;
        while (current->next) {
            current = current->next;
        }
        current->next = newNode;
    }
}

// Function to remove and return the token from the head of the list
/**
 * @brief Removes and returns the token from the head of the list.
 *
 * This function removes the head node from the linked list and returns its token.
 *
 * @param head A reference to the head pointer of the linked list.
 * @return The token from the removed head node.
 */
std::string pop(Node*& head) {
    if (!head) {
        return "";
    }
    Node* temp = head;
    std::string token = temp->token;
    head = head->next;
    delete temp;
    return token;
}

// Function to free all nodes in the list
/**
 * @brief Frees all nodes in the list.
 *
 * This function deallocates memory for all nodes in the linked list, effectively clearing the list.
 *
 * @param head A reference to the head pointer of the linked list.
 */
void freeList(Node*& head) {
    while (head) {
        Node* temp = head;
        head = head->next;
        delete temp;
    }
}

// Function to print all tokens in the list
/**
 * @brief Prints all tokens in the list.
 *
 * This function iterates through the linked list and prints each token to the standard output.
 *
 * @param head A pointer to the head of the linked list.
 */
void printList(Node* head) {
    Node* current = head;
    while (current) {
        std::cout << current->token;
        if (current->next) {
            std::cout << "\n";
        }
        current = current->next;
    }
}

// Function to get the nth token from the list
/**
 * @brief Gets the nth token from the list.
 *
 * This function returns the token at the specified position in the linked list.
 *
 * @param head A pointer to the head of the linked list.
 * @param n The position of the token to retrieve (0-based index).
 * @return The token at the specified position, or an empty string if the position is out of bounds.
 */
std::string getNthToken(Node* head, int n) {
    Node* current = head;
    int i = 0;
    while (current) {
        if (i == n) {
            return current->token;
        }
        current = current->next;
        i++;
    }
    return ""; // if n is greater than the number of tokens
}

// Function to remove leading spaces from a string
/**
 * @brief Removes leading spaces from a string.
 *
 * This function returns a new string with all leading whitespace characters removed from the input string.
 *
 * @param str The input string.
 * @return A new string with leading spaces removed.
 */
std::string removeLeadingSpaces(const std::string& str) {
    size_t start = 0;
    while (start < str.size() && std::isspace(static_cast<unsigned char>(str[start]))) {
        start++;
    }
    return str.substr(start);
}

// Function to tokenize the input string and store tokens in the list
/**
 * @brief Tokenizes the input string and stores tokens in the list.
 *
 * This function splits the input string into tokens based on spaces and stores each token in the linked list.
 * It also sets the run_bg flag if the "&" token is encountered.
 *
 * @param istream The input string to be tokenized.
 * @param head A reference to the head pointer of the linked list.
 */
void tokenize(const std::string& istream, Node*& head) {
    std::string input = removeLeadingSpaces(istream);
    size_t start = 0;
    size_t end = input.find(' ');

    while (end != std::string::npos) {
        std::string token = input.substr(start, end - start);
        if (token == "&") {
            run_bg = 1;
        } else {
            enqueue(head, token);
        }
        start = end + 1;
        end = input.find(' ', start);
    }

    std::string token = input.substr(start);
    if (token == "&") {
        run_bg = 1;
    } else {
        enqueue(head, token);
    }
}

// Function to tokenize the input string considering quoted strings and store tokens in the list
/**
 * @brief Tokenizes the input string considering quoted strings and stores tokens in the list.
 *
 * This function splits the input string into tokens, taking into account quoted strings, and stores each token in the linked list.
 * It also sets the run_bg flag if the "&" token is encountered.
 *
 * @param istream The input string to be tokenized.
 * @param head A reference to the head pointer of the linked list.
 */
void tokenize2(const std::string& istream, Node*& head) {
    std::string token;
    bool inQuotes = false;

    for (char ch : istream) {
        if (ch == '\"' || ch == '\'') {
            inQuotes = !inQuotes;
        } else if (ch == ' ' && !inQuotes) {
            if (!token.empty()) {
                if (token == "&") {
                    run_bg = 1;
                } else {
                    enqueue(head, token);
                }
                token.clear();
            }
        } else {
            token += ch;
        }
    }

    if (inQuotes) {
        std::cerr << "Missing closing quote\n";
        freeList(head);
        return;
    }

    if (!token.empty()) {
        if (token == "&") {
            run_bg = 1;
        } else {
            enqueue(head, token);
        }
    }
}
