
coinbase                      exos 
                        OS           program
   |                     |              |
   |			 |      	|------> program sets up websocket library objects and uses
   |			 |<-------------| 	 those to initate a connection; this calls out to the 
   |			 | | netstack	|
   |			 |------------->|------> OS opens up a socket for the host addr and port 
   |			 |      	| 	 and begins listening in the background then returns control
   |			 |		|	 
   |)<--------tcp------>(|      	|------> after some time we get a stream between the computers
   |			 |		|   					
   |			 |      	|------> program uses websocket library to send request
   |			 |<-------------|  	 for ticker updates, the OS get control and issues the req
   |			 | | netstack 	|
   |)<------req---------(|------------->|------> after sending the req the OS returns control to the program
   |		         | 		| 	
   |)-------json------->(|      	|------> upon coinbase sending data, the OS begins bufferring data in the background
   |			 | 		|		
   |			 |<-------------|------> program issues a read() call, desiring access to buffer, this
   |			 |      	| 	 becomes a syscall, we context switch and transfer control to 
   |			 |		| 	 the OS which begins copying the buffer into program memory
   |			 |      	|
   |			 |------------->|------> once complete, the OS relinquishes control to the program which
   |			 |		| 	 begins ORE-ifying the data