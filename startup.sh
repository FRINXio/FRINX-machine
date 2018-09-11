#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

# Common functions
script="startup.sh"

function example {
    echo -e "example: $script -m"
}

function usage {  
 echo -e "usage: $script [OPTION]  \n"  
}

function help {
  usage
    echo -e "OPTION:"
    echo -e "  -m | --minimal   Start with minimal resource usage and frinxit disabled."
    echo -e "\n"
  example
}

function check_success {
  if [[ $? -ne 0 ]] 
  then
  RED='\033[0;31m'
  NC='\033[0m' # No Color
  printf "${RED}System is not healthy. Shutting down.\n${NC}"
  echo "Removing containers."
  ./teardown.sh
  exit
fi
}



# Loop arguments
minimal=false
while [ "$1" != "" ];
do
case $1 in
    -m | --minimal)
    minimal=true
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


# Start odl
if [ "$minimal" = true ]; then
  sudo docker-compose -f docker-compose.min.yml up -d odl
else
  sudo docker-compose up -d odl
fi

# Wait to start
echo 'Wait 30s to start'
sleep 30

# Wait till it responds
./health_check.sh --odl
check_success $?

# Start other containers
if [ "$minimal" = true ]; then
  sudo docker-compose -f docker-compose.min.yml up -d
else
  sudo docker-compose up -d
fi


# Wait for containers to start
echo 'Wait 30s for other containers to start.'
sleep 30


### Health check
./health_check.sh
check_success $?


# Import Frinx Tasks and Workflow defs
sudo docker exec -it micros bash -c "cd /home/app && newman run netinfra_utils/postman.json --folder 'SETUP' -e netinfra_utils/postman_environment.json"
check_success $?


echo 'Startup finished!'





