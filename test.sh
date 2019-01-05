#!/bin/sh

./ganache.sh &>/dev/null &
sleep 5

py.test --cov=pymaker --cov-report=term --cov-append tests/

