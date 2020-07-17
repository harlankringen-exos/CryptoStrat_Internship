# CryptoStrat_Internship

## Preliminary
Get all the packages and such out of the way.  

1. we have abandoned the idea of a virtual environment

2. pip3 install copra # open source library mentioned in coinbase docs

3. pip3 install websockets # widely used implementation of websockets protocol

4. pip3 install ipython

5. pip3 install jupyter

6. pip3 install pandas

7. pip3 install matplotblib

8. pip3 install Pillow

9. pip3 install pyinstrument

10. pip3 install msgpack

11. pip3 install pycallgraph

12. pip3 install pyprof2calltree

13. sudo apt install kcachegrind

14. sudo apt install linux-tools-common linux-tools-4.15.0-106-generic linux-tools-generic

## Project Organization

In pursuit of python best practices, we follow a project structure based on this
outline:

https://dev.to/codemouse92/dead-simple-python-project-structure-and-imports-38c6

The "app" is called `connector` and code lives in the various subdirectories of
`connector/`.  The `infrastructure` dir is used to hold copies of an open source
library which were useful in getting up to speed on websockets.  The `socks` dir
holds a minimal implementation of an approach just using asncio and websockets.
The `requests` dir is just a holding ground for json requests to be sent to the
exchange.

## How to run

At the project root, where `connector/` and `README.md` are sitting, run the
following at a shell:

`python3 -m connector "matches.json" "outfile.txt"`

The first argument refers to a json file in the `requests/` directory while the
second is just the name of the desired outfile.

This looks for `__main__.py` which currently calls the `tester.py` code in `socks/`.

## Profiling This article talks about syncing up with C and the `rdtsc` assembly
instruction
https://hacks.mozilla.org/2020/05/building-functiontrace-a-graphical-python-profiler/
although we haven't played around with it.

`python3 -m cProfile connector/app.py "level2.json"`

`python3 -m pyinstrument connector/app.py "level2.json"`

## Notes about Portabiilty and Python Versions

The state of python is a little strange, with multiple versions (even in the 3.x
range), including the fact that the installer can be different, `pip` v. `pip3`.
With a full application ready to be run, this can be solved with a container
solution, e.g. docker.

I don't have that set up yet, so you might need to manually fix python
version/dependency problems.