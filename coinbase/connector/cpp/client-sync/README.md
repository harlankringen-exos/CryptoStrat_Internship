
# What is it

Synchronous websocket client that runs locally.  It sends a string given by a
command line argument that, if greater than 1, will trigger the corresponding
server to begin sending coinbase messages. The client processes these messages
by transforming them to ORE and then msgpacking them.  They are not written to
file or anything after.

It is meant to be paired with the server.

# How do you use it

`cmake -Bbin -H. && cmake --build bin`

`websocket-msg-client-sync 0.0.0.0 8080 hello`

This will spin up the client and shoot off the string to the server.

# Dependencies

This depends on the boost library, msgpack-c, and rapidjson.  I installed all of
these locally in the parent directory under "include/", e.g. cpp/include/rapidjson.
