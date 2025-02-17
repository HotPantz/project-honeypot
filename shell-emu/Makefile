# Source files
SRC=src/fshell.cpp src/shell_parser.cpp src/logger.cpp src/main.cpp

# Target to build the fshell executable
fshell: $(SRC)
	sudo g++ -lcurl -Wall $(SRC) -o /usr/bin/fshell

# Target to clean up the build
clean:
	sudo rm -f /usr/bin/fshell