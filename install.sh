#!/bin/bash

set -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

script="install.sh"

#Declare the number of mandatory args
margs=1

# Common functions
function example {
    echo -e "example: $script -l license_token -b odl kibana"
}

function usage {
    echo -e "usage: $script OPTIONS [services] \n"
    echo -e "If no services are specified all are pulled or built."
    echo -e "Services: odl micros conductor-server dynomite elasticsearch kibana sample-topology logstash uniconfig-ui"
}

function help {
  usage
    echo -e "OPTIONS:"
    echo -e "  -l | --license  <VALUE>    Specify custom license.
            Saves license token to [PATH to git repo]/odl/frinx.license.cfg.
            If license file exists, custom odl license is applied after each pull"
    echo -e "  -b | --build               Build specified services locally"
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

file=odl/frinx.license.cfg
valid_images=("odl" "micros" "conductor-server" "dynomite" "elasticsearch" "kibana" "sample-topology" "logstash" "uniconfig-ui")
license=
license_flag=false
build=false

# Args while-loop
while [ "$1" != "" ];
do
case $1 in
   -l | --license )
   license_flag=true
   shift
   license=$1
   ;;
   -b | --build )
   build=true
   ;;
   -h | --help )
   help
   exit
   ;;
   *)
   valid "$1" "${valid_images[@]}"
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

# Save license to file
if [ "$license_flag" = true ]
then
      echo "token=$license" > $file
fi

# Update submodules
git submodule init
git submodule update --recursive --remote

cd conductor
echo 'git.root=../../' > gradle.properties
echo "submodVersion=$(git for-each-ref refs/tags --sort=-taggerdate --format='%(tag)' | grep -v -m 1 'frinx' | cut -d "v" -f 2)" >> gradle.properties

cd ${DIR}
if [ "$build" = false ]; then
  echo 'Pull images'
  sudo docker-compose pull "${input_containers[@]}"

  # Copy custom license if file exists
  if [[ -f "$file" ]]; then
    echo "Apply license from file $file"
    sudo docker-compose build odl
  fi
else
  echo 'Build images'
  sudo docker-compose build "${input_containers[@]}"
fi

# Clean up
sudo docker system prune -f
