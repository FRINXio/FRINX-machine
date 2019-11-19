#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )"/workflows && pwd )

function help {
  usage
    echo -e "OPTION:"
    echo -e "  -l | --local      Import from localhost"
    echo -e "\n"
  example
}

function import_workflows {

for file in "$DIR"/*; do
	echo $file
    BODY=$( cat $file) 

    curl -X PUT -H "Content-Type: application/json" -d "[$BODY]" http://$host:8080/api/metadata/workflow
    echo " "
done
}

host=conductor-server
while [ "$1" != "" ];
do
case $1 in
    -l | --local)
    host=localhost
    shift
    ;;
    -h | --help )
    help
    exit
    ;;
    *)    # unknown option
    echo "$script: illegal option $1"
    exit 1 #error
    ;;
esac
done

import_workflows

echo 'Import finished!'
