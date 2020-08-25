
# What is it

Websocket server that runs locally.  Once it receives a string of length greater
than 1, it will start sending json messages either encoded in variables or from file.
It will send messages to the address and port given as command line arguments.

It is meant to be paired with the client-sync or client-async clients.  They
will connect to the server in the appropriate way

# How do you use it

`cmake -Bbin -H. && cmake --build bin`

`websocket-msg-server 0.0.0.0 8080`

This will run the server in the background which will initially do nothing,
waiting to receive a small bit of text to command it to begin streaming coinbase
messages.

# Dependencies

The server depends on the boost library, which I installed locally in the cpp directory (e.g. cpp/include/boost_1_73_0).
