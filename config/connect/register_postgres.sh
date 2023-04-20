#!/bin/bash

# set sensitive env variables from docker secrets
if [[ -f "/set_env_secrets.sh" ]]; then
  . /set_env_secrets.sh ''
fi

CONF_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ) 
response_code=""

pushd ${CONF_DIR} > /dev/null || exit 1
while true
do
  response_code=$(curl -X POST -o /dev/null -sw '%{http_code}' -H "Content-Type:application/json" http://localhost:8083/connectors/ -d "$(envsubst < register-postgres.json)")
  echo "$response_code"
  if [[ "$response_code" == "201" || "$response_code" == "409" ]]; then
    echo "Received status code: $response_code. Task completed"
    break
  fi
  sleep 1
done
popd > /dev/null || exit 1
