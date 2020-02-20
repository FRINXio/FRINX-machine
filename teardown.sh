#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

script="teardown.sh"

# Common functions
function usage {
    echo -e "Usage: $script [-v|--volumes] [-i|--images]\n"
}

function help {
    usage
    echo -e "OPTIONS:"
    echo -e "  -v | --volumes             Removes volumes specified in the docker-compose.*.yml file"
    echo -e "  -i | --images              Removes all images used by any service specified in the docker-compose.*.yml file"
    echo -e "\n"
}


VOLUMES=""
IMAGES=""

# Args while-loop
while [ "$1" != "" ];
do
case $1 in
   -v | --volumes )
   VOLUMES="--volumes"
   ;;
   -i | --images )
   IMAGES="--rmi all"
   ;;
   -h | --help )
   help
   exit
   ;;
   *)
    echo "Unknown option: '$1'"
    help
    exit
   ;;
esac
shift
done

### Stop and remove containers, optionally also volumes and images
docker-compose -f docker-compose.bridge.yml down $VOLUMES $IMAGES --remove-orphans
