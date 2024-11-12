# Source files
SRC=src/fshell.cpp src/shell_parser.cpp

# Target to build the fshell executable
fshell : 
	g++ -Wall $(SRC) -o bin/fshell

# Target to clean up the build
clean : rm bin/fshell