#!/bin/bash

# set -e

# If the docker image doesn't already exist, pull it from docker hub
result=$( docker images -q makerdao/testchain-pymaker:unit-testing )
if [[ "$result" == "" ]]; then
    echo Docker image not found\; pulling from docker hub
    docker pull makerdao/testchain-pymaker:unit-testing
fi

# Start ganache; record the PID so it can be cleanly stopped after testing
./ganache.sh &>/dev/null &
GANACHE_PID=$!
echo Started ganache as pid $ganache_pid

# Start the docker image and wait for parity to initialize
docker-compose up -d
sleep 2

# Run the tests
py.test --cov=pymaker --cov-report=term --cov-append tests/
TEST_RESULT=$?

# Cleanup
pkill -P $GANACHE_PID
echo Stopping container
docker-compose down

exit $TEST_RESULT
