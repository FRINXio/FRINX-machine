#!/bin/bash

set -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

script="install.sh"

#Declare the number of mandatory args
margs=1

# Common functions
function example {
    echo -e "example: $script -l VAL"
}

function usage {
    echo -e "usage: $script MANDATORY \n"
}

function help {
  usage
    echo -e "MANDATORY:"
    echo -e "  -l | --license  VAL     License token"
    echo -e "  -p | --preserveUI      Do not delete UI images"
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



# Main
margs_precheck $# $1

license=
preserve=true

# Args while-loop
while [ "$1" != "" ];
do
case $1 in
   -l | --license )
   shift
   license=$1
   ;;
   -p | --preserve )
   preserve=false
   ;;
   -h | --help )
   help
   exit
   ;;
   *)             
   echo "$script: illegal option $1"
   help
   exit 1 # error
   ;;
esac
shift
done

# Pass here your mandatory args for check
margs_check $license


# Write license to file
echo "token=$license" > odl/frinx.license.cfg

# Removed odl ui image
if [ "$preserve" = true ]; then
	sudo docker rmi conductor:ui || true
	sudo docker rmi $(sudo docker images -q frinx/conductor-ui_base) || true
fi

# Update submodules
git submodule init
git submodule update --recursive --remote



# Build docker images
cd ${DIR}
echo 'Create external volume for redis'
sudo docker volume create --name=redis_data
sudo docker volume create --name=elastic_data
echo 'Build images'
sudo docker-compose build









