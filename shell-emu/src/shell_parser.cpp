// XX-XX-2023 Frederic MUSIAL made the shell parser

#include "../headers/shell_parser.hpp"
#include <string>
#include <iostream>
#include <cctype>

extern int run_bg;

// Function to create a new node with the given token
Node* createNode(const std::string& token) {
    return new Node(token);
}

// Function to add a new node with the given token to the end of the list
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
void freeList(Node*& head) {
    while (head) {
        Node* temp = head;
        head = head->next;
        delete temp;
    }
}

// Function to print all tokens in the list
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
std::string removeLeadingSpaces(const std::string& str) {
    size_t start = 0;
    while (start < str.size() && std::isspace(static_cast<unsigned char>(str[start]))) {
        start++;
    }
    return str.substr(start);
}

// Function to tokenize the input string and store tokens in the list
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