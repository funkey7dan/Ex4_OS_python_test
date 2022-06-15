CC = gcc

CFLAGS = -w

all:
	$(CC) $(CFLAGS) ex4_srv.c -o ex4_srv.o 
	$(CC) $(CFLAGS) ex4_client.c -o ex4_client.o
	
ex4_srv.o: ex4_srv.c
	$(CC) $(CFLAGS) ex4_srv.c -o ex4_srv.o

ex4_client.o: ex4_srv.c
	$(CC) $(CFLAGS) ex4_client.c -o ex4_client.o
	
