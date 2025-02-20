# Source files
SRC=src/fshell.cpp src/shell_parser.cpp src/logger.cpp src/main.cpp

# Target to build the fshell executable
fshell: $(SRC)
	sudo g++ -Wall $(SRC) -o /usr/bin/fshell -lcurl

# Target to clean up the build
clean:
	sudo rm -f /usr/bin/fshell