#!/bin/bash

# Pull the docker image
docker pull makerdao/testchain-pymaker:unit-testing

# Start ganache; record the PID so it can be cleanly stopped after testing
command -v ganache-cli >/dev/null 2>&1 || { echo >&2 "Please install ganache before running tests"; exit 1; }
./ganache.sh &>/dev/null &
GANACHE_PID=$!
echo Started ganache as pid $ganache_pid

# Start the docker image and wait for parity to initialize
docker-compose up -d
sleep 2

# Run the tests
py.test --cov=pymaker --cov-report=term --cov-append tests/ $@
TEST_RESULT=$?

# Cleanup
pkill -P $GANACHE_PID
echo Stopping container
docker-compose down

exit $TEST_RESULT
