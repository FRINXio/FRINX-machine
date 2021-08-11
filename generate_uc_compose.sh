#!/bin/bash

show_help()
{
local ___script_name="$(basename "${0}")"
cat << EOF
DESCRIPTION:
 Create compose file for specific uniconfig instances
 Each service must have unique name. 
 These compose files can be stored to any folder and then can be
 started witg FRINX-Machine ./startup.sh --multinode <PATH>

OPTIONS:

 ${___script_name} [OPTIONS]

  FRINX-MACHINE CONFIGURATION

   -s|--service-name [UNICONFIG-SERVICE-NAME]
                     - Unique uniconfig service name

   -i|--instances    [__UC_INSTANCES]
                     - Default : 2

   -n|--node-id      [SWARM-NODE-ID]
                     - Define swarm node id

   -f|--folder-path  [UNICONFIG FOLDER PATH]
                     - Define path, where will be 
                       compose file stored. 
                          
  COMMON SETTINGS

   -h|--help    Print this help and exit
   -d|--debug   Enable verbose

EOF
}


function argumentsCheck {

if [ "$#" -eq 0 ]
then
    show_help
    exit 1
fi

while [ $# -gt 0 ]
do
    case "${1}" in
        -h|--help) 
            show_help
            exit 0;;

        -s|--service-name)
            if [[ ${2} != "-"* ]] && [[ ! -z ${2} ]]; then
                checkUniconfigServiceName "${2}"
                __SERVICE_NAME="${2}"
                shift
            else
                echo "Service name not defined. See help!"
                exit 1
            fi;;

        -n|--node-id)
            if [[ ${2} != "-"* ]] && [[ ! -z ${2} ]]; then
                __NODE_ID="${2}"; shift
            else
                echo "Service swarm node id not defined. See help!"
                exit 1
            fi;;

        -i|--instances)
            local regex='^[0-9]+$'
            if [[ ${2} =~ ${regex} ]]; then
                __UC_INSTANCES="${2}"; shift
            else
                echo -e "${ERROR} Bad instances input defined. See help!"
                exit 1
            fi;;

        -f|--folder-path)

            if [[ ${2} != "-"* ]] && [[ ! -z ${2} ]] && [[ -d ${2} ]] ; then
                __FOLDER_PATH="$(readlink -f ${2})"; shift
            else
                echo -e "${ERROR} Bad folder path defined. See help!"
                exit 1
            fi;;

        -d|--debug) 
            set -x;;
            
        *) 
            echo -e "Unknown argument option! ${1} \nSee '${__SCRIPT_NAME} --help'"
            exit 1;;
    esac
    shift
done
}


function checkUniconfigServiceName {
  local __service_name="${1}"
  local regex='^[a-z0-9_-]*$'
  echo -e "${INFO} Verify Uniconfig service name: ${__service_name}"
  if [[ "${__service_name}" =~ ${regex} ]]; then
    echo -e "${OK} Uniconfig service name: ${__service_name}"
  else
    echo -e "${ERROR} Uniconfig service name '${__service_name}' contain illegal characters"
    echo -e "${ERROR} Allowed characters are:   a-z 0-9 _- "
    exit 1
  fi
}

function isNodeInSwarm {
  if [[ "$(docker node ls -f id=${1} --format {{.ID}})" == "${1}" ]]; then
      echo -e "${INFO} Node" ${1} "in swarm - Hostname: $(docker node ls -f id=${1} --format {{.Hostname}})"
  else 
      echo -e "${WARNING} Node ${1} not in swarm"
  fi
}

function prepareConfigFiles {

    local __CONFIG_PATH="${__DEF_CONFIG_PATH}/${__SERVICE_NAME}"
    local __DEF_UC_CONFIG_MIDDLE_PATH="config/uniconfig/frinx/uniconfig"

    # prepare traefik config files
    mkdir -p "${__FOLDER_PATH}/${__CONFIG_PATH}/traefik" "${__FOLDER_PATH}/${__CONFIG_PATH}/${__UNICONFIG_SERVICE_SUFIX}"
    cp ${FM_DIR}/config/traefik/* "${__FOLDER_PATH}/${__CONFIG_PATH}/traefik"
    sed -i "s/  uniconfig:/  ${__SERVICE_FULL_NAME}:/g" "${__FOLDER_PATH}/${__CONFIG_PATH}/traefik/traefik.yml"

    # prepare uniconfig config files
    rsync -r --exclude "cache/*" ${FM_DIR}/${__DEF_UC_CONFIG_MIDDLE_PATH}/* "${__FOLDER_PATH}/${__CONFIG_PATH}/${__UNICONFIG_SERVICE_SUFIX}"
    chmod a+w "${__FOLDER_PATH}/${__CONFIG_PATH}/${__UNICONFIG_SERVICE_SUFIX}/cache"
}


function generateUcCompose {

    if [[ "${__SERVICE_NAME}" == "uniconfig" ]]; then
        __SERVICE_FULL_NAME="${__UNICONFIG_SERVICE_SUFIX}"
    else
        __SERVICE_FULL_NAME="${__SERVICE_NAME}-${__UNICONFIG_SERVICE_SUFIX}"
    fi

    local __COMPOSE_PATH="${__FOLDER_PATH}/${__UC_COMPOSE_NAME}"
    local __CONFIG_PATH="${__DEF_CONFIG_PATH}/${__SERVICE_NAME}"

    prepareConfigFiles

    cp "${FM_COMPOSE_DIR}/${__UC_COMPOSE_NAME}" "${__COMPOSE_PATH}"

    # service names
    sed -i "s/  uniconfig:/  ${__SERVICE_NAME}:/g" "${__COMPOSE_PATH}"
    sed -i "s/  uniconfig-controller:/  ${__SERVICE_FULL_NAME}:/g" "${__COMPOSE_PATH}"
    sed -i "s/  uniconfig-postgres:/  ${__SERVICE_NAME}-postgres:/g" "${__COMPOSE_PATH}"

    # swarm node id
    sed -i 's|${UC_SWARM_NODE_ID}|'"${__NODE_ID}|g" "${__COMPOSE_PATH}"
    sed -i 's|${UF_SWARM_NODE_ID}|'"${__NODE_ID}|g" "${__COMPOSE_PATH}"

    # swarm config paths
    sed -i 's|${UC_CONFIG_PATH}|'"/${__CONFIG_PATH}/${__UNICONFIG_SERVICE_SUFIX}|g" "${__COMPOSE_PATH}"
    sed -i 's|${UF_CONFIG_PATH}/traefik|'"/${__CONFIG_PATH}/traefik|g" "${__COMPOSE_PATH}"

    # swarm persistant volume paths
    sed -i 's|uniconfig-controller_logs|'"${__SERVICE_FULL_NAME}_logs|g" "${__COMPOSE_PATH}"
    sed -i "s/uniconfig-postgresql_data/${__SERVICE_NAME}-postgresql_data/g" "${__COMPOSE_PATH}"

    # swarm uniconfig-controller replicas
    sed -i 's|replicas: ${UC_CONTROLLER_REPLICAS:-1}|'"replicas: ${__UC_INSTANCES}|g" "${__COMPOSE_PATH}"

    # labels
    sed -i 's|entrypoints=https,uniconfig|'"entrypoints=https,${__SERVICE_NAME}|g" "${__COMPOSE_PATH}"
    sed -i 's|\.uniconfig\.|'"\.${__SERVICE_NAME}\.|g" "${__COMPOSE_PATH}"

    # env
    sed -i 's|_host=uniconfig-postgres|'"_host=${__SERVICE_NAME}-postgres|g" "${__COMPOSE_PATH}"
}

function prepareFolder {
    if [ -d ${__FOLDER_PATH} ]; then
        rm -rf ${__FOLDER_PATH}/*
        mkdir -p ${__FOLDER_PATH}/${__DEF_CONFIG_PATH}
    fi
}


# =======================================
# Program starts here
# =======================================

ERROR="\033[0;31m[ERROR]:\033[0;0m"
WARNING="\033[0;33m[WARNING]:\033[0;0m"
INFO="\033[0;96m[INFO]:\033[0;0m"
OK="\033[0;92m[OK]:\033[0;0m"

FM_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
FM_COMPOSE_DIR="${FM_DIR}/composefiles"

__SERVICE_NAME="uniconfig-controller"
__FOLDER_PATH="${FM_COMPOSE_DIR}/uniconfig"

__UC_COMPOSE_NAME="swarm-uniconfig.yml"

__DEF_CONFIG_PATH="opt/frinx"

__UC_INSTANCES=2
__UNICONFIG_SERVICE_SUFIX="uniconfig-controller"

argumentsCheck "$@"
prepareFolder
isNodeInSwarm ${__NODE_ID}
generateUcCompose
