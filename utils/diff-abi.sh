#!/bin/bash

# This script is useful when updating ABIs as newer contracts are released.
vimdiff <(git show HEAD:pymaker/abi/$@ | jq '.') <(jq '.' < $@)
