#include "../headers/shell_parser.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>

Node* head = NULL; //liste chainee d'arguments
char* args[MAX_ARGS], *command, *outputFile = NULL, *inputFile = NULL, *errFile = NULL;
int run_bg = 0; //flag pour lancer en arrière-plan

void doexec(void){
    char* token;
    int i = 0, pipefd[2];
    args[0] = command;
    while(head != NULL){
        token = pop(&head);
        /*  on pop les tokens tant que on n'atteint pas > < ou | (ce sont alors des arguments)
            ou tant qu'on ne vide pas la liste (1 seule commande + arguments)*/
        if(strcmp(token, ">") == 0){ //outfile
            outputFile = pop(&head);
            continue;
        }
        else if(strcmp(token, "<") == 0){ //infile
            inputFile = pop(&head);
            continue;
        }
        else if(strcmp(token, "2>") == 0){ //errfile
            errFile = pop(&head);
            continue;
        }
        else if(strcmp(token, "|") == 0){ //pipe
            //printf("pipe detected!\n");
            token = pop(&head); //next command

            if(token == NULL || head == NULL){
                fprintf(stderr,"No command after pipe\n");
                exit(EXIT_FAILURE);
            }

            pipe(pipefd);
            pid_t pid = fork();
            switch(pid){
                case -1:
                    perror("Fork error\n");
                    break;
                case 0: /* execution de la commande suivante */
                    head = NULL;
                    dup2(pipefd[1], 1);
                    close(pipefd[0]);
                    close(pipefd[1]);
                    break;
                default: /* on redirige la sortie de la commande qui suit le | vers l'entrée de la commande 1 */
                    dup2(pipefd[0], 0);
                    close(pipefd[0]);
                    close(pipefd[1]);
                    i = 0;
                    command = token;
                    break;
            }
        }
        else //simple command + arguments
            args[++i] = token;
    }

    if(i < MAX_ARGS) /* check if we aren't out of bounds of the args array */
        args[++i] = NULL;
    else{
        fprintf(stderr,"Too many arguments\n");
        exit(EXIT_FAILURE);
    }
                        
    if(outputFile != NULL){
    /*  ouvrir en readonly, créer si n'existe pas, tronquer si existe 
        avec les autorisations ecriture & lecture pour le user */
        int fd = open(outputFile, O_WRONLY|O_CREAT|O_TRUNC, S_IRUSR | S_IWUSR); 
        if(fd == -1){
            perror("Couldn't open output file\n");
            exit(EXIT_FAILURE);
        }
        if(dup2(fd, STDOUT_FILENO) == -1){
            perror("Couldn't duplicate file descriptor\n");
            exit(EXIT_FAILURE);
        }
        close(fd);
    }
    else if(inputFile != NULL){
        int fd = open(inputFile, O_RDONLY);
        if(fd == -1){
            perror("Couldn't open input file\n");
            exit(EXIT_FAILURE);
        }
        if(dup2(fd, STDIN_FILENO) == -1){
            perror("Couldn't duplicate file descriptor\n");
            exit(EXIT_FAILURE);
        }
            close(fd);
        }
    else if(errFile != NULL){
        int fd = open(errFile, O_WRONLY|O_CREAT|O_TRUNC, S_IRUSR | S_IWUSR);
        if(fd == -1){
            perror("Couldn't open error file\n");
            exit(EXIT_FAILURE);
        }
        if(dup2(fd, STDERR_FILENO) == -1){
            perror("Couldn't duplicate file descriptor\n");
            exit(EXIT_FAILURE);
        }
        close(fd);
    }

    execvp(command, args);
    fprintf(stderr,"Couldn't execute %s\n", command);
    exit(EXIT_FAILURE);
    return;
}

int main(int argc, char* argv[]){

    char* istream = NULL, *cwd = NULL;
    istream = (char*) malloc(MAX_INPUT_LEN*sizeof(char));

    while(1){
        cwd = getcwd(cwd, MAX_DIR_LEN); //répertoire courant
        
        if(cwd == NULL){
            fprintf(stderr,"Couldn't get current working directory\n");
            printf("\033[1m%%\033[0m ");
        }
        else{
            printf("\033[1m%s \033[34m%%\033[0m\033[0m ", cwd);
        }
        if(fgets(istream, MAX_INPUT_LEN, stdin) == NULL){ //recupère l'entrée & check si CTRL+D
            return 0;
        }

        char *newline = strchr(istream, '\n'); //enlève le newline pour pouvoir faire strcmp correctement
        if(newline) 
            *newline = '\0';
        
        tokenize2(istream, &head);
        
        if(head == NULL){ //si la liste est vide, on recommence une entrée
            continue;
        }
        else{
            command = pop(&head);
            /* On interprète exit ou cd séparémment aux autres commandes */
            if(strcmp(command, "exit") == 0){
                if(head != NULL)
                    freeList(&head);
                if(istream != NULL)
                    free(istream);
                if(cwd != NULL)
                    free(cwd);
                return 0;
            }
            else if(strcmp(command, "cd") == 0){
                char* dir = pop(&head); //récupère le répertoire
                if(dir == NULL){
                    fprintf(stderr,"No directory specified\n");
                }
                else{
                    if(chdir(dir) == -1)
                        perror("Couldn't change directory - doesn't exist\n");
                }
                free(dir);
            }
            else{
                pid_t pid = fork();
                switch(pid){
                    case -1:
                        perror("Fork error\n");
                        break;
                    
                    case 0: /* execution de la commande */
                        doexec();
                        break;
                    
                    default: /* processus père */
                        if(!run_bg){
                                waitpid(pid, NULL, 0);
                        }
                        run_bg = 0;
                        break;
                }
            }
        }
        if(head != NULL)
            freeList(&head);
    }    
    return 0;
}
