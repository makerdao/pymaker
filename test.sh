#!/bin/sh

./ganache.sh &
GANACHE_PID=$!
sleep 5

py.test --cov=pymaker --cov-report=term --cov-append tests/

kill -9 $GANACHE_PID