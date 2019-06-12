#!/bin/sh

# set -e

./ganache.sh &>/dev/null &
docker-compose up -d
sleep 5

py.test --cov=pymaker --cov-report=term --cov-append tests/test_dss.py

kill $(lsof -t -i tcp:8555)
echo Stopping container
docker-compose down
