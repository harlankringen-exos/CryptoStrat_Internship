
# Investigating the Use of C++ on the Coinbase Code

This directory tracks the attempts to translate the code in `connector/socks/*` into C++.

## Dependencies

1. boost (beast and asio)
2. nlohmann (json)
3. msgpack

## How to build

This is a work in progress as I move from my local machine to a remote machine.
The above libraries need to be installed and the CmakeLists.txt should change,
but that's it.  There is a lot of info in the CMakeLists.txt that can also
probably be removed.

The most glaring is that msgpack-c is a git submodule which needs to be pulled
out into something more self-contained.

The `include/` directory contains a clone of the `beast` library but the code
uses the version in the adjacent `boost` library.

`cmake -Bbin -H. && cmake --build bin`

## Project Structure

Also WIP.  After a bit more tinkering I will orgranize it into something more
classically application-like.

Right now, the `src/client-async`, `src/client-sync`, and `src/server` contain
the main bits of code.  They are all ripped from `beast` examples.  The server
can be spun up in a shell and will block for connections.  The clients may be
run from shells which try to connect. The server will wait for a "hello" message
after all the handshaking prompting it to write 10,000 json messages to the
connection.

They should all be compactifid into a single directory.  

## SSL

The client-(a)sync and server examples are meant to be run together, as opposed
to running the coinbase client against the server.  This is because the server
doesn't do as much SSL business, I think.  Should be an easy fix, but for not
the three clients must unfortunately all be kept in sync.