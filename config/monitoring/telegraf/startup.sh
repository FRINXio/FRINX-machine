#!/bin/bash

# set sensitive env variables from docker secrets
if [[ -f "/set_env_secrets.sh" ]]; then
  . /set_env_secrets.sh ''
fi

# remove manager configuration for non manager instances
if [[ "${HOSTNAME}" != "${MANAGER_HOSTNAME}" ]]; then
    sed -i '/# MANAGER/,$d'  telegraf.conf
fi

telegraf "$@"
