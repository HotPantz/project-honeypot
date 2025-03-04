#include "../headers/shell_parser.hpp"
#include <string>
#include <iostream>
#include <cctype>

extern int run_bg;

//creates a new node containing the provided token
Node* createNode(const std::string& token){
    return new Node(token);
}

//appends a token to the end of the linked list
void enqueue(Node*& head, const std::string& token){
    Node* newNode = createNode(token);
    if(!head){
        head = newNode;
    } 
    else{
        Node* current = head;
        while(current->next){
            current = current->next;
        }
        current->next = newNode;
    }
}

//removes and returns the first token in the list
std::string pop(Node*& head){
    if(!head){
        return "";
    }
    Node* temp = head;
    std::string token = temp->token;
    head = head->next;
    delete temp;
    return token;
}

//deallocates all nodes in the list
void freeList(Node*& head){
    while (head)
    {
        Node* temp = head;
        head = head->next;
        delete temp;
    }
}

//outputs all tokens line by line
void printList(Node* head){
    Node* current = head;
    while(current)
    {
        std::cout << current->token;
        if(current->next){
            std::cout << "\n";
        }
        current = current->next;
    }
}

//retrieves the token at position n (0-indexed)
std::string getNthToken(Node* head, int n){
    Node* current = head;
    int i = 0;
    while(current)
    {
        if(i == n){
            return current->token;
        }
        current = current->next;
        i++;
    }
    return ""; // if n is greater than the number of tokens
}

//trims spaces from beginning of string
std::string removeLeadingSpaces(const std::string& str){
    size_t start = 0;
    while(start < str.size() && std::isspace(static_cast<unsigned char>(str[start]))){
        start++;
    }
    return str.substr(start);
}

//basic tokenizer that splits input by spaces
void tokenize(const std::string& istream, Node*& head){
    std::string input = removeLeadingSpaces(istream);
    size_t start = 0;
    size_t end = input.find(' ');

    while (end != std::string::npos)
    {
        std::string token = input.substr(start, end - start);
        if(token == "&"){
            run_bg = 1; //set background execution flag
        } 
        else{
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

//advanced tokenizer that preserves quoted strings
void tokenize2(const std::string& istream, Node*& head){
    std::string token;
    bool inQuotes = false;

    for(char ch : istream){
        if(ch == '\"' || ch == '\''){
            inQuotes = !inQuotes; //toggle quote state
        } 
        else if(ch == ' ' && !inQuotes)
        { //space outside quotes delimits tokens
            if(!token.empty())
            {
                if(token == "&"){
                    run_bg = 1;
                } 
                else{
                    enqueue(head, token);
                }
                token.clear();
            }
        }
        else{
            token += ch;
        }
    }

    if(inQuotes) //handle unclosed quotes
    {
        std::cerr << "Missing closing quote\n";
        freeList(head);
        return;
    }

    if(!token.empty()) //handle final token
    {
        if(token == "&"){
            run_bg = 1;
        } 
        else{
            enqueue(head, token);
        }
    }
}