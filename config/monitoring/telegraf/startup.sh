#!/bin/bash

CONFIG_FILE="/etc/telegraf/telegraf.conf"
TMP_CONFIG_FILE="/tmp/telegraf.conf"

echo "Moving ${CONFIG_FILE} to ${TMP_CONFIG_FILE}"
cp ${CONFIG_FILE} ${TMP_CONFIG_FILE}

# set sensitive env variables from docker secrets
if [[ -f "/set_env_secrets.sh" ]]; then
  . /set_env_secrets.sh ''
fi

# remove manager configuration for non manager instances
if [[ "${HOSTNAME}" != "${MANAGER_HOSTNAME}" ]]; then
    echo "Remove manager configuration from ${TMP_CONFIG_FILE}"
    sed -i '/# MANAGER/,$d'  ${TMP_CONFIG_FILE}
fi

cat ${TMP_CONFIG_FILE}
telegraf --config ${TMP_CONFIG_FILE} "$@"
