# CryptoStrat_Internship

## Install Log

### Preliminary

1. We're using python3 in a virtualenv

2. We're using anaconda (sequestered in a virtual env); Anaconda is installed
locally on my machine but we ignore this in commits, deferring portable
packaging/dockerizing until later.

### Initial Setup (venv)

1. `apt-get install python3-venv`

2. `python3 -m venv .venv`

3. to enter and leave respectively:

`source .venv/bin/activate`

`deactivate`

### Anaconda
https://docs.anaconda.com/anaconda/install/linux/

1. `apt-get install libgl1-mesa-glx libegl1-mesa libxrandr2 libxrandr2 libxss1
libxcursor1 libxcomposite1 libasound2 libxi6 libxtst6`

### FeatureMine
[ ] todo
https://wiki.featuremine.com/index.php?title=Getting_Started

1. `apt-get install -y zlib1g-dev libdw-dev libunwind-dev`

2. `pip install pytz msgpack kafka-python`

3. ```curl http://mirror.cedia.org.ec/nongnu/numdiff/numdiff-5.9.0.tar.gz -o numdiff-5.9.0.tar.gz
    tar -xvzf numdiff-5.9.0.tar.gz
    cd numdiff-5.9.0
    ./configure
    make
    make install
    ```

4. `pip install extractor-4.1.7-cp36-cp36m-linux_x86_64.whl yamal-4.1.7-cp36-cp36m-linux_x86_64.whl`

5. `pip install jubilee-4.1.7-cp36-cp36m-linux_x86_64.whl`


** Restart

1. no venv

2. pip3 install copra

3. pip3 install websockets

4. pip3 install ipython

5. pip3 install jupyter

6. pip3 install pandas

7. pip3 install matplotblib

8. pip3 install Pillow 