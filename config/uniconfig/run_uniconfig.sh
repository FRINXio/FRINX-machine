#!/bin/bash

CONFIG="config/lighty-uniconfig-config.json"
JAR_DIRS="./*:./libs/*:./config"
MAIN_CLASS="io.frinx.lighty_uniconfig.Main"
JAVA_MAX_MEM=${JAVA_MAX_MEM:="4G"}
DEBUG_PARAMETER="--debug"
UNICONFIG_ID=${CONTAINER_ID:=1}

# set sensitive env variables from docker secrets
if [[ -f "/set_env_secrets.sh" ]]; then
  . /set_env_secrets.sh ''
fi

if [[ -d "/opt/uniconfig-frinx/cache_tmp" ]]; then
  echo "Copy cache_tmp folder before start"
  cp -R /opt/uniconfig-frinx/cache_tmp/* /opt/uniconfig-frinx/cache
fi

display_usage() {
    echo -e "Usage: $(basename "$0") [-f] [-l LICENSE_TOKEN] [--debug]"
    echo -e "where: "
    echo -e "   -l LICENSE_TOKEN : license token for running Frinx Uniconfig"
    echo -e "   -f               : new license token is forced (overwrites old license)"
    echo -e "   --debug          : enabled java debugging on port 5005"
}

is_enabled_debugging() {
  for arg in "$@"; do
    if [ "$arg" = $DEBUG_PARAMETER ]; then
      return 1
    fi
  done
  return 0
}

delete_debug_argument() {
  filtered_args=("$@")
  for i in "${!filtered_args[@]}"; do
    if [ "${filtered_args[i]}" = "$DEBUG_PARAMETER" ]; then
      unset 'filtered_args[i]'
    fi
  done
}

for i in "$@"
do
case $i in
    -h|--help)
    display_usage
    exit 0
    ;;
esac
done

# removing cached data and logs from previous run
rm -rf snapshots/ journal/

# folder where lighty stores data
mkdir -m 700 -p data

is_enabled_debugging "$@"; enabled_debugging=$?
if [ $enabled_debugging -eq 1 ]; then
  delete_debug_argument "$@"
  java "-Xmx${JAVA_MAX_MEM}" -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005 -cp "${JAR_DIRS}" \
    "${MAIN_CLASS}" -c "${CONFIG}" "${filtered_args[@]}"; unset filtered_args
else
  java "-Xmx${JAVA_MAX_MEM}" -cp "${JAR_DIRS}" "${MAIN_CLASS}" -c "${CONFIG}" "$@"
fi
unset enabled_debugging
