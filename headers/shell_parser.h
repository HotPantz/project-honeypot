#ifndef SHELL_PARSER_H
#define SHELL_PARSER_H

#define MAX_ARGS 51 // 50 arguments + NULL

// 4096 + '\0'
#define MAX_TOKEN_LEN 4097

#define MAX_INPUT_LEN 8192
#define MAX_DIR_LEN 4097

typedef struct Node{
    char token[MAX_TOKEN_LEN];
    struct Node* next;
}Node;

/*  Decompose l'entree en tokens (si separes par des espaces) 
    et crée une liste chainée les contenant */ 
void tokenize(char* istream, Node** head);

/*  Décompose l'entrée en tokens comme tokenize mais prend
    en compte les guillemets : ' ' et " " */
void tokenize2(char* istream, Node** head);

/*  Supprime les espaces avant la commande  */
char* removeLeadingSpaces(char* str);

/* Récupère le premier token de la liste et le supprime */
char* pop(Node** head);

/* Ajoute un token à la fin de la liste */
void enqueue(Node** head, char* token);

void freeList(Node** head);

/*  Récupère le n-ieme token dans la liste
    Si n > nb. tokens : renvoie NULL, renvoie le token sinon */
char* getNthToken(Node* head, int n);

/* Affiche la liste des tokens (debug) */
void printList(Node* head);

/* Crée une cellule de liste contenant le token */
Node* createNode(char* token);

#endif