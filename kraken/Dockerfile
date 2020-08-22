FROM python:3.7 AS base

WORKDIR /home
COPY ./src ./src
COPY setup.py ./
RUN python setup.py sdist

FROM aurotfp/fm_executor:4.6.0_1.0.0

ARG PIP_URL

RUN apt-get update && apt-get install -y moreutils jq
RUN pip install --extra-index-url ${PIP_URL} featuremine exos-cdm-cli cdm-metadata-client==0.2.39 --upgrade

WORKDIR /home
COPY --from=base /home/dist/coinbase_ore_gen*.tar.gz ./
RUN pip install --extra-index-url ${PIP_URL} coinbase_ore_generator*.tar.gz
