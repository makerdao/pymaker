#!/bin/bash

# set -e

# If the docker image doesn't already exist, load it from the tarball
result=$( docker images -q mcd-testchain )
if [[ "$result" == "" ]]; then
    echo Docker image not found\; loading from tarball
    gunzip -kf tests/config/mcd-testchain.tar.gz
    docker load -q < tests/config/mcd-testchain.tar
fi

# Start ganache; record the PID so it can be cleanly stopped after testing
./ganache.sh &>/dev/null &
ganache_pid=$(pgrep -f node)
echo Started ganache as pid $ganache_pid

# Start the docker image and wait for parity to initialize
docker-compose up -d
sleep 2

# Run the tests
echo py.test --cov=pymaker --cov-report=term --cov-append tests/test_dss.py

# Cleanup
kill $ganache_pid
echo Stopping container
docker-compose down
