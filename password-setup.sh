#!/usr/bin/env bash

# this path is mounted as a volume in docker-compose
PASSWORD_FILE_PATH="/opt/odl_pass/db-credentials.txt"

# these values are loaded from a file, that can be found on the volume mounted
# from docker
USERNAME=$(cat "${PASSWORD_FILE_PATH}" | grep "username" | cut -d ":" -f 2 )
PASSWORD=$(cat "${PASSWORD_FILE_PATH}" | grep "password" | cut -d ":" -f 2 )

FILE_TO_UPDATE="generateMount.sh"
TMP="$(cd / ; find . -iname "${FILE_TO_UPDATE}")"
PATH_OF_FILE_TO_UPDATE="$(echo "${TMP:1}")"


sed -i "s/USERNAME=\"\"/USERNAME=\"${USERNAME}\"/" "${PATH_OF_FILE_TO_UPDATE}"
sed -i "s/PASSWORD=\"\"/PASSWORD=\"${PASSWORD}\"/" "${PATH_OF_FILE_TO_UPDATE}"
