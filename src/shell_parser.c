#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <ctype.h>
#include "../headers/shell_parser.h"

extern int run_bg;

Node* createNode(char* token){
    Node* newNode = (Node*)malloc(sizeof(Node));
    if(newNode == NULL){
        fprintf(stderr, "Unable to allocate memory for new node\n");
        exit(EXIT_FAILURE);
    }
    strcpy(newNode->token, token);
    newNode->next = NULL;

    return newNode;
}

void enqueue(Node** head, char* token){
    Node* newNode = createNode(token);
    if(*head == NULL)
        *head = newNode;
    else{
        Node* current = *head;
        while(current->next != NULL){
            current = current->next;
        }
        current->next = newNode;
    }
}
char* pop(Node** head){
    if(*head == NULL)
        return NULL;
    Node* temp = *head;
    char* token = strdup(temp->token);
    *head = (*head)->next;
    free(temp);
    return token;
}

void freeList(Node** head){
    Node* current = *head;
    Node* next;
    while(current != NULL){
        next = current->next;
        free(current);
        current = next;
    }
    *head = NULL;
}

void printList(Node* head){
    Node* current = head;
    //int test = 0;
    while(current != NULL){
        printf("%s", current->token);
         if(current->next != NULL) {
            printf("\n");
        }
        current = current->next;
        //test++;
    }
    //printf("Number of tokens: %d\n", test);
}

char* getNthToken(Node* head, int n){
    Node* current = head;
    int i = 0;
    while(current != NULL){
        if(i == n)
            return current->token;
        current = current->next;
        i++;
    }
    return NULL; //si n est plus grand que le nombre de tokens
}

char* removeLeadingSpaces(char* str){
    while(isspace((unsigned char)*str)) str++;
    return str;
}

void tokenize(char* istream, Node** head){
    char* token;
    istream = removeLeadingSpaces(istream);
    while((token = strsep(&istream, " "))){
        if(strcmp(token, "&") == 0)
            run_bg = 1;
        else{ //ajout du token à la fin de la liste
            Node* newNode = createNode(token);
            if(*head == NULL)
            *head = newNode; 
            else{
                Node* current = *head;
                while(current->next != NULL){
                    current = current->next;
                }
                current->next = newNode;
            }
        }
    }
}

void tokenize2(char* istream, Node** head){
    char* token = (char*)malloc((2*(strlen(istream) + 1))*sizeof(char)); //pire des cas: 1 token prend toute la ligne
    int tokenIndex = 0;
    int inQuotes = 0;

    for(int i = 0; istream[i] != '\0'; i++){
        if(istream[i] == '\"' || istream[i] == '\''){
            if(!inQuotes) //Si on n'est pas déjà dans des guillemets - inversion de l'état
                inQuotes = 1;
            else
                inQuotes = 0;
        }
        else if(istream[i] == ' ' && !inQuotes){ //Si on rencontre un espace en dehors des guillemets
            if(tokenIndex > 0){ //Si on a un token à ajouter
                token[tokenIndex] = '\0'; //on doit terminer le token par \0, car on le reconstruit caractère par caractère
                if(strcmp(token, "&") == 0)
                    run_bg = 1;
                else{
                    Node* newNode = createNode(token);
                    if(*head == NULL)
                    *head = newNode; 
                    else{
                        Node* current = *head;
                        while(current->next != NULL){
                            current = current->next;
                        }
                        current->next = newNode;
                    }
                }
                tokenIndex = 0; //Token ajouté - reset du compteur
            }
        }
        else{
            token[tokenIndex++] = istream[i]; //on reconstruit le token caractère par caractère
        }
    }
    
    //Cas où il manque le " à la fin
    if(inQuotes){
        fprintf(stderr, "Missing closing quote\n");
        if(*head != NULL)
            freeList(head);
        return;
    }

    if(tokenIndex > 0){ // S'il y a un token à la fin de la ligne
        token[tokenIndex] = '\0';
        if(strcmp(token, "&") == 0)
            run_bg = 1;
        else{    
            Node* newNode = createNode(token);
            if(*head == NULL)
                *head = newNode; 
            else{
                Node* current = *head;
                while(current->next != NULL){
                    current = current->next;
                }
                current->next = newNode;
            }
        }
    }
    /*if(token != NULL)
        free(token);*/
}