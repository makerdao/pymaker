#!/bin/sh

./ganache.sh &>/dev/null &
GANACHE_PID=$!
sleep 5

py.test --cov=pymaker --cov-report=term --cov-append tests/
TEST_RESULT=$?

pkill -P $GANACHE_PID

exit $TEST_RESULT
