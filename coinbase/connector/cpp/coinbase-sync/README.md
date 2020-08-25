
# What is it

This is a secure, synchronous websocket client that listens to the public coinbase exchange server.

# How do I use it

`cmake -Bbin -H. && cmake --build bin`

`timeout 60s bin/websocket-msg-client-sync "false"`

This employs the `timeout` command to send a SIGTERM to the client after 60
seconds.  The command may be run without the signal handler in which case you
may kill it with the usual ctrl-c.  Once the signal is caught the program writes
a global store of data to file, specifically creating a `summary.txt` and
`timing.csv`.  The timing data contains the data in the following form:

"msg_type, processing_time_ns, buff_read_ns".

The signal handler was added to do timing tests for a variety of durations
easily.  In redesigning this I would probably move to a class that represented a
connection and keep an internal timer that would do the same thing.

# Dependencies

This depends on the boost library, as well as msgpack-c and rapidjson.  The
CMakeLists.txt file assumes they are in a parent directory labeled "include".

Additionally, the program depends on openssl, zlib, and dl, which I installed at
root system level.

# Other notes

The <host> in this case is "ws-feed.prime.coinbase.com" and the <port> for secure
websocket connections is always 443, both of which we hardcode in the program.


