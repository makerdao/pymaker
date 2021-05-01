#!/bin/bash

# Pull the docker image
docker pull makerdao/testchain-pymaker:unit-testing

# Remove existing container if tests not gracefully stopped
docker-compose down

# Start ganache
docker-compose up -d ganache

# Start parity and wait to initialize
docker-compose up -d parity
sleep 2

# Run the tests
py.test --cov=pymaker --cov-report=term --cov-append tests/test_auctions.py tests/test_cdpmanager.py \
 tests/test_dsrmanager.py tests/test_dss.py tests/test_savings.py tests/test_shutdown.py $@
TEST_RESULT=$?

# Cleanup
docker-compose down

exit $TEST_RESULT
