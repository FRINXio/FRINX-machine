#!/bin/bash

set -e

function help {
    echo -e "Creates temporary container. Attaches uniconfig_logs volume and copies logs dir to local dir."
    echo -e "OPTIONS: No options available"
}

while [ "$1" != "" ];
do
case $1 in
   * )
   help
   exit
   ;;
esac
shift
done


echo "Create temporary container to mount uniconfig_logs volume to"
container_id=$(docker container create -v uniconfig_logs:/uniconfig_logs busybox)

echo "Copy data from volume to current directory"
docker cp  $container_id:/uniconfig_logs .


echo "Remove temp container"
docker rm $container_id
