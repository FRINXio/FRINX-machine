#!/bin/bash

CONFIG="config/lighty-uniconfig-config.json"
JAR_DIRS="./*:./libs/*:./config"
MAIN_CLASS="io.frinx.lighty_uniconfig.Main"
JAVA_MAX_MEM=${JAVA_MAX_MEM:="4G"}
DEBUG_PARAMETER="--debug"
UNICONFIG_ID=${CONTAINER_ID:=1}
PROXY_ENABLED=${PROXY_ENABLED:="false"}

# set sensitive env variables from docker secrets
if [[ -f "/set_env_secrets.sh" ]]; then
  . /set_env_secrets.sh ''
fi

display_usage() {
    echo -e "Usage: $(basename "$0") [-f] [-l LICENSE_TOKEN] [--debug]"
    echo -e "where: "
    echo -e "   -l LICENSE_TOKEN : license token for running Frinx Uniconfig"
    echo -e "   -f               : new license token is forced (overwrites old license)"
    echo -e "   --debug          : enabled java debugging on port 5005"
}

is_system_proxy_enabled() {
    unset PROXY_PORT PROXY_HOST
    local PROXY_URL="$1"
    if [[ "${PROXY_URL}" == "http"* ]] && [[ $(echo "${PROXY_URL}" | tr -d -c ":" | wc -m) -eq 2 ]]; then
        PROXY_PORT="$(echo "${PROXY_URL}"| cut -d ':' -f 3 | sed 's,[^0-9]*,,g')"
        PROXY_HOST="$(echo "${PROXY_URL}"| cut -d ':' -f 2 | sed 's,//,,')"
    elif [[ "${PROXY_URL}" =~ ^[[:digit:]] ]] && [[ $(echo "${PROXY_URL}" | tr -d -c ":" | wc -m) -eq 1 ]]; then
        PROXY_PORT="$(echo "${PROXY_URL}"| cut -d ':' -f 2 | sed 's,[^0-9]*,,g')"
        PROXY_HOST="${PROXY_HOST}$(echo "${PROXY_URL}"| cut -d ':' -f 1)"
    else
        echo -e ${ERROR} "Used bad HTTP Proxy format ${PROXY_URL}"
        exit 1
    fi
    eval "$3=-D${2}.proxyHost=${PROXY_HOST}"
    eval "$4=-D${2}.proxyPort=${PROXY_PORT}"
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

if [[ ${PROXY_ENABLED} == "true" ]]; then
  is_system_proxy_enabled $HTTP_PROXY "http" __HTTP_HOST __HTTP_PORT
  is_system_proxy_enabled $HTTPS_PROXY "https" __HTTPS_HOST __HTTPS_PORT
  _JAVA_OPTIONS="$_JAVA_OPTIONS ${__HTTP_HOST} ${__HTTP_PORT} ${__HTTPS_HOST} ${__HTTPS_PORT} -Dhttp.nonProxyHosts=${NO_PROXY}"
fi

# removing cached data and logs from previous run
rm -rf snapshots/ journal/

# folder where lighty stores data
mkdir -m 700 -p data

# wait for postgresql container
sleep 5

is_enabled_debugging "$@"; enabled_debugging=$?
if [ $enabled_debugging -eq 1 ]; then
  delete_debug_argument "$@"
  java "-Xmx${JAVA_MAX_MEM}" -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005 -cp "${JAR_DIRS}" \
    "${MAIN_CLASS}" -c "${CONFIG}" "${filtered_args[@]}"; unset filtered_args
else
  java "-Xmx${JAVA_MAX_MEM}" -cp "${JAR_DIRS}" "${MAIN_CLASS}" -c "${CONFIG}" "$@"
fi
unset enabled_debugging
