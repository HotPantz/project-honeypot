# Source files
SRC=src/fshell.cpp src/shell_parser.cpp src/logger.cpp src/main.cpp

# Target to build the fshell executable
fshell: $(SRC)
	g++ -lcurl -Wall $(SRC) -o bin/fshell

# Target to clean up the build
clean:
	rm -f bin/fshell