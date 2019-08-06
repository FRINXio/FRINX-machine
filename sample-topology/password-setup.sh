#!/usr/bin/env bash

# this path is mounted as a volume in docker-compose
PASSWORD_FILE_PATH="/opt/odl_pass/db-credentials.txt"

# these values are loaded from a file, that can be found on the volume mounted
# from docker
USERNAME=$(cat "${PASSWORD_FILE_PATH}" | grep "username" | cut -d ":" -f 2 )
PASSWORD=$(cat "${PASSWORD_FILE_PATH}" | grep "password" | cut -d ":" -f 2 )

FILE_TO_UPDATE="generateMount.sh"
PATH_OF_FILE_TO_UPDATE="cli-testtool/util/${FILE_TO_UPDATE}"

sed -i "s/USERNAME=\"admin\"/USERNAME=\"${USERNAME}\"/" "${PATH_OF_FILE_TO_UPDATE}"
sed -i "s/PASSWORD=\"admin\"/PASSWORD=\"${PASSWORD}\"/" "${PATH_OF_FILE_TO_UPDATE}"
