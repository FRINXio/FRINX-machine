#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}


sudo docker-compose up -d

### Wait for containers to start
echo 'Wait 30s for containers to start.'
sleep 30


### Health check
./health_check.sh
if [[ $? -ne 0 ]]
then
  RED='\033[0;31m'
  NC='\033[0m' # No Color
  printf "${RED}System is not healthy. Shutting down.\n${NC}"
  echo "Removing containers."
  ./teardown.sh
  exit
fi



### Import Frinx Tasks and Workflow defs
docker exec -it micros bash -c "cd /home/app && newman run netinfra_utils/postman.json --folder 'SETUP' -e netinfra_utils/postman_environment.json"


echo 'Startup finished!'




