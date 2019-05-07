#!/bin/bash

vimdiff <(git show HEAD:pymaker/abi/$@ | jq '.') <(jq '.' < $@)
