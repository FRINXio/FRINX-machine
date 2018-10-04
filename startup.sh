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
    echo -e "  -m | --minimal   Start with lower resource usage."
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

function start_container {
if [ "$minimal" = true ]; then
  sudo docker-compose -f docker-compose.min.yml up -d "$1"
else
  sudo docker-compose -f docker-compose.yml up -d "$1"
fi
}

function start_containers {
local containers_to_start=("odl" "dynomite" "elasticsearch" "kibana" "conductor-server" "frinxit" "micro"  "conductor-ui" "sample-topology" )

for i in "${containers_to_start[@]}"; do 

start_container $i
./health_check.sh $i
check_success $?
echo "################"
done

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


start_containers



# Import Frinx Tasks and Workflow defs
sudo docker exec -it micros bash -c "cd /home/app && newman run netinfra_utils/postman.json --folder 'SETUP' -e netinfra_utils/postman_environment.json"
check_success $?


echo 'Startup finished!'





