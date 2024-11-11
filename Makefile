SRC=src/fshell.cpp src/shell_parser.cpp

fshell : 
	g++ -Wall $(SRC) -o fshell

clean : 
	rm fshell
