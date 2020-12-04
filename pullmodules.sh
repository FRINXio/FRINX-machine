#!/bin/bash

repoUrl='https://github.com/FRINXio/'
repos="api-gateway conductor uniflow-micros schellar uniflow-api uniflow-ui"

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}/build

# Initial folder cleanup
find . -maxdepth 1 ! -name README | xargs rm -rf

# Clone repos
for var in $repos
do
    git clone $repoUrl$var $var
done
