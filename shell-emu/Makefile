SRC=src/fshell.cpp src/shell_parser.cpp src/logger.cpp src/main.cpp

fshell: $(SRC)
	sudo g++ -Wall $(SRC) -o /usr/bin/fshell -lcurl

clean:
	sudo rm -f /usr/bin/fshell