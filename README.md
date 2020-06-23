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

3. (again, because several files were missing, such as `activate` inside .venv/bin
`python3 -m venv new_strat` 

4. to enter and leave respectively:
`source new_strat/bin/to leave:
`deactivate`

### Anaconda
https://docs.anaconda.com/anaconda/install/linux/

1. $ apt-get install libgl1-mesa-glx libegl1-mesa libxrandr2 libxrandr2 libxss1
libxcursor1 libxcomposite1 libasound2 libxi6 libxtst6

2. bash ~/Downloads/Anaconda3-2020.02-Linux-x86_64.sh
> installation finished.
> Do you wish the installer to initialize Anaconda3
> by running conda init? [yes|no]
> [no] >>> 
> You have chosen to not have conda modify your shell scripts at all.
> To activate conda's base environment in your current shell session:
> 
> eval "$(/home/aik/exos_internship/anaconda3/bin/conda shell.YOUR_SHELL_NAME hook)" 
> 
> To install conda's shell functions for easier access, first activate, then:
> 
> conda init

> If you'd prefer that conda's base environment not be activated on startup, 
>    set the auto_activate_base parameter to false: 

> conda config --set auto_activate_base false

### FeatureMine
[ ] todo
https://wiki.featuremine.com/index.php?title=Getting_Started

1. apt-get install -y zlib1g-dev libdw-dev libunwind-dev

2. pip install pytz msgpack kafka-python

3. curl http://mirror.cedia.org.ec/nongnu/numdiff/numdiff-5.9.0.tar.gz -o numdiff-5.9.0.tar.gz
    tar -xvzf numdiff-5.9.0.tar.gz
    cd numdiff-5.9.0
    ./configure
    make
    make install

4. pip install extractor-4.1.7-cp36-cp36m-linux_x86_64.whl yamal-4.1.7-cp36-cp36m-linux_x86_64.whl

5. pip install jubilee-4.1.7-cp36-cp36m-linux_x86_64.whl