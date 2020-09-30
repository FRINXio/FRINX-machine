#!/bin/bash

set -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

script="install.sh"

#Declare the number of mandatory args
margs=1

# Common functions
function example {
    echo -e "example: $script -b uniconfig kibana"
}

function usage {
    echo -e "usage: $script OPTIONS [services] \n"
    echo -e "If no services are specified all are pulled or built."
    echo -e "Services: uniconfig micros conductor-server dynomite postgresql elasticsearch kibana logstash uniconfig-ui"
}

function help {
  usage
    echo -e "OPTIONS:"
    echo -e "  -b | --build               Build specified services locally"
    echo -e "  -d | --dev                 Updates submodules to latest, else does nothing with submodules"
    echo -e "\n"
  example
}

# Ensures that the number of passed args are at least equals
# to the declared number of mandatory args.
# It also handles the special case of the -h or --help arg.
function margs_precheck {
	if [ $2 ] && [ $1 -lt $margs ]; then
		if [ $2 == "--help" ] || [ $2 == "-h" ]; then
		    help
	            exit
		else
	    	    usage
	    	    exit 1 # error
		fi
	fi
}

# Ensures that all the mandatory args are not empty
function margs_check {
	if [ $# -lt $margs ]; then
	    help
	    exit 1 # error
	fi
}


# function to check if array contains argument
#valid element array
function valid {
  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1
}

valid_containers=("uniconfig" "micros" "conductor-server" "dynomite" "postgresql" "elasticsearch" "kibana" "logstash" "uniconfig-ui" "uniconfig-api" "uniflow-ui" "uniflow-api" "dashboard" "api-gateway" "portainer")
build=false
dev_flag=false

# Args while-loop
while [ "$1" != "" ];
do
case $1 in
   -b | --build )
   build=true
   ;;
   -d | --dev )
   dev_flag=true
   ;;
   -h | --help )
   help
   exit
   ;;
   *)
   valid "$1" "${valid_containers[@]}"
    if [[ $? -eq 0 ]];
    then
        input_containers+=( "$1" )
    else
    echo "$script: container '$1' not known"
        exit 1
    fi
   ;;
esac
shift
done


if [ "$dev_flag" = true ]
then
    # Update submodules
    #git submodule init
    git submodule update --init --recursive --remote

    cd conductor
    echo 'git.root=../../' > gradle.properties
    echo "submodVersion=$(git for-each-ref refs/tags --sort=-taggerdate --format='%(tag)' | grep -v -m 1 'frinx' | cut -d "v" -f 2)" >> gradle.properties
else
    # we need to init submodules even when images are just pulled
    # from docker hub because of the bug in docker-compose
    # https://github.com/docker/compose/issues/3513
    git submodule update --init --recursive --remote
fi


cd ${DIR}
if [ "$build" = false ]; then
  echo 'Pull images'
  docker-compose -f docker-compose.bridge.yml pull "${input_containers[@]}"
else
  echo 'Build images'
  docker-compose -f docker-compose.bridge.yml build "${input_containers[@]}"
fi

# Clean up
docker system prune -f
