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
                __SERVICE_NAME="${2}"; shift
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

        -f|--folder-path)
            if [[ ${2} != "-"* ]] && [[ ! -z ${2} ]] && [[ -d ${2} ]] ; then
                __FOLDER_PATH="${2}"; shift
            else
                echo "Bad folder path defined. See help!"
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

function isNodeInSwarm {
  if [[ "$(docker node ls -f id=${1} --format {{.ID}})" == "${1}" ]]; then
      echo -e "${INFO} Node" ${1} "in swarm - Hostname: $(docker node ls -f id=${1} --format {{.Hostname}})"
  else 
      echo -e "${WARNING} Node ${1} not in swarm"
  fi
}

function createUniconfigCompose {

    local __SERVICE_PATH="${__FOLDER_PATH}/swarm-${__SERVICE_NAME}.yml"

    cp ${FM_DIR}/composefiles/swarm-uniconfig.yml "${__SERVICE_PATH}"
    sed -i "s/ uniconfig:/ ${__SERVICE_NAME}:/g" "${__SERVICE_PATH}"
    sed -i "s/ uniconfig-postgres:/ ${__SERVICE_NAME}-postgres:/g" "${__SERVICE_PATH}"
    sed -i "s/_host=uniconfig-postgres/_host=${__SERVICE_NAME}-postgres/g" "${__SERVICE_PATH}"
    sed -i 's|\${UC_CONFIG_PATH}|/opt/frinx/uniconfig|g' "${__SERVICE_PATH}"
    sed -i 's|${UC_SWARM_NODE_ID}|'"${__NODE_ID}|g" "${__SERVICE_PATH}"
}

# =======================================
# Program starts here
# =======================================

ERROR="\033[0;31m[ERROR]:\033[0;0m"
WARNING="\033[0;33m[WARNING]:\033[0;0m"
INFO="\033[0;96m[INFO]:\033[0;0m"
OK="\033[0;92m[OK]:\033[0;0m"

scriptName="$(basename "${0}")"
FM_DIR="$(dirname "$(readlink -f "${scriptName}")")"

argumentsCheck "$@"

isNodeInSwarm ${__NODE_ID}
createUniconfigCompose