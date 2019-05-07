#!/bin/sh

set -e

./ganache.sh &>/dev/null &
sleep 5
docker-compose up -d

py.test --cov=pymaker --cov-report=term --cov-append tests/

kill $(lsof -t -i tcp:8555)
sleep 1
docker-compose down
