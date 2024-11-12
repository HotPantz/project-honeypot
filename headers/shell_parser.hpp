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

/*  Décompose l'entrée en tokens (si séparés par des espaces) 
    et crée une liste chaînée les contenant */ 
void tokenize(const std::string& istream, Node*& head);

/*  Décompose l'entrée en tokens comme tokenize mais prend
    en compte les guillemets : ' ' et " " */
void tokenize2(const std::string& istream, Node*& head);

/*  Supprime les espaces avant la commande  */
std::string removeLeadingSpaces(const std::string& str);

/* Récupère le premier token de la liste et le supprime */
std::string pop(Node*& head);

/* Ajoute un token à la fin de la liste */
void enqueue(Node*& head, const std::string& token);

/* Libère la mémoire de tous les noeuds de la liste */
void freeList(Node*& head);

/*  Récupère le n-ième token dans la liste
    Si n > nb. tokens : renvoie une chaîne vide, sinon renvoie le token */
std::string getNthToken(Node* head, int n);

/* Affiche la liste des tokens (utilisé pour le debug) */
void printList(Node* head);

/* Crée une cellule de liste contenant le token */
Node* createNode(const std::string& token);

#endif // SHELL_PARSER_HPP
