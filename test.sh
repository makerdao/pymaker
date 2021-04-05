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

# HACK: Enable the token faucet
export DEPLOYMENT_ADDRESS=0x00a329c0648769A73afAc7F9381E08FB43dBEA72
export FAUCET=0x0A64DF94bc0E039474DB42bb52FEca0c1d540402
seth send -F $DEPLOYMENT_ADDRESS -S /dev/null --keystore=tests/config/keys/UnlimitedChain \
  $FAUCET 'hope(address)' 0x0000000000000000000000000000000000000000

# Run the tests
py.test --cov=pymaker --cov-report=term --cov-append tests/ $@
TEST_RESULT=$?

# Cleanup
docker-compose down

exit $TEST_RESULT
