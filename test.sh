#!/bin/sh

TESTRPC_GAS_LIMIT=7000000 py.test --cov=pymaker --cov-report=term --cov-append tests/
