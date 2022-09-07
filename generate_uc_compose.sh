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

   -f|--folder-path  [UNICONFIG FOLDER PATH]
                     - Define path, where will be 
                       compose file stored. 

    SWARM NODE-PLACEMENT CONFIGURATION 

     --force           [__FORCE_GENERATE]
                       - Allow re/generation of composefile with wrong parameters
                       - Default '${__FORCE_GENERATE}'

                 [USE ONLY ONE OPTION]

     -n|--node-id      [TYPE]
                       - Define services placement by node id
     --hostname        [TYPE]
                       - Define services placement by node hostname
     --label           [TYPE]
                       - Define services placement by node zone label
     --role            [TYPE]
                       - Define services placement by node role

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
                __SERVICE_NAME_DEFINED='true'
                shift
            else
                echo "Service name not defined. See help!"
                exit 1
            fi;;

        -n|--node-id|--hostname|--label|--role)
            if [ -z ${__only_one_config} ]; then
              if [ ${1} == "-n" ]; then
                __only_one_config="true"
                TYPE="id"
              elif [ ${1} == "--node-id" ]; then
                __only_one_config="true"
                TYPE="id"
              elif [ ${1} == "--hostname" ]; then
                __only_one_config="true"
                TYPE="name"
              elif [ ${1} == "--label" ]; then
                __only_one_config="true"
                TYPE="node.label"
              elif [ ${1} == "--role" ]; then
                __only_one_config="true"
                TYPE="role"
              fi

              if [[ ${2} == '-'* ]] || [[ ${2} == '' ]] || [[ -z ${2}  ]]; then
                echo -e "${ERROR} Missing Swarm node placement input parameter for deployment: '${1}', type: 'node ${TYPE}'"
                exit 1
              else
                __NODE_ID=${2}
                shift
              fi
            else
                echo -e "${ERROR} Conflict parameters: -n|--node-id|--hostname|--label|--role !!! Just one can be selected !!!"
                echo -e "Use '${scriptName} --help' for more details"
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

        --force)
          SWARM_STATUS=${WARNING}
          __FORCE_GENERATE='true';;

        -d|--debug) 
            set -x;;
            
        *) 
            echo -e "Unknown argument option! ${1} \nSee '${__SCRIPT_NAME} --help'"
            exit 1;;
    esac
    shift
done

if [[ -z $TYPE ]]; then
  echo -e "${ERROR} Node placement type not defined. See help !!!"
  exit 1
fi

if [[ -z $__SERVICE_NAME_DEFINED ]]; then
  echo -e "${ERROR} Service name not defined. See help !!!"
  exit 1
fi


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

  bold=$(tput bold)
  normal=$(tput sgr0) 

  if [[ $TYPE == 'node.label' ]]; then
    node_hostname=($(docker node ls -f ${TYPE}=zone=${1} --format {{.Hostname}})) || 
      { { echo -e "${ERROR} Bad node definition parameter ${bold}${TYPE}=${1}${normal}";} ;}
    db_node_hostname=$(docker node ls -f ${TYPE}=db=${1} --format {{.Hostname}})
    if [[ ${db_node_hostname} == '' ]] || [[ $( echo ${db_node_hostname} | tr -cd ' ' | wc -c) -ne 0 ]]; then
      echo -e "${SWARM_STATUS} Only one node can have ${TYPE}=db=${1}"
      if [[ $__FORCE_GENERATE == 'false' ]]; then
        echo -e "${SWARM_STATUS} Composefiles was not generated"
        exit 1
      fi
      echo -e "${SWARM_STATUS} Composefiles will be force-generated with wrong placement settings for db"
    fi
  else
    node_hostname=($(docker node ls -f ${TYPE}=${1} --format {{.Hostname}})) || 
      { { echo -e "${ERROR} Bad node definition parameter ${bold}${TYPE}=${1}${normal}";} ;}
  fi
  
  if [[ $node_hostname != '' ]] || [[ $__FORCE_GENERATE == 'true' ]] ; then

    case $TYPE in
    'id')
        node=$(docker node inspect ${node_hostname} --format {{.ID}})
        message="with ID"
        deployment="node.id == ${1}"
        deployment_psql="node.id == ${1}"
        ;;

    'name')
        for i in "${node_hostname[@]}"; do
          node=$(docker node inspect ${node_hostname} --format {{.Description.Hostname}})
          message="with hostname"
          deployment="node.hostname == ${1}"
          deployment_psql="node.hostname == ${1}"
          if [[ $node != "" ]]; then
            break 
          fi 
        done
        ;;

    'node.label')
        for i in "${node_hostname[@]}"; do
          node=$(docker node inspect ${i} --format {{.Spec.Labels.zone}})
          message="with label zone ="
          deployment="node.labels.zone == ${1}"
          deployment_psql="node.labels.db == ${1}"
          if [[ $node != "" ]]; then
            break 
          fi 
        done
        ;;

    'role')
        for i in "${node_hostname[@]}"; do
          node=$(docker node inspect ${node_hostname} --format {{.Spec.Role}})
          message="with role"
          deployment="node.role == ${1}"
          deployment_psql="node.role == ${1}"
          if [[ $node != "" ]]; then
            break 
          fi 
        done
        ;;

    *)
        echo -e "${ERROR} ${TYPE} is not supported"
        exit 1
        ;;
    esac
  fi

  if [[ "${node}" == "${1}" ]]; then
      echo -e "${INFO} Node ${message} ${bold}${1}${normal} is in swarm - Hostname: ${bold}${node_hostname}${normal}"
  else 
      echo -e "${SWARM_STATUS} Node ${message} ${bold}${1}${normal} not in swarm"
      if [[ $__FORCE_GENERATE == 'false' ]]; then
        echo -e "${SWARM_STATUS} Composefiles was not generated"
        exit 1
      fi
      echo -e "${SWARM_STATUS} Composefiles were force-generated with wrong placement settings"
  fi
}

function prepareConfigFiles {

    local __CONFIG_PATH="${__DEF_CONFIG_PATH}/${__SERVICE_NAME}"
    local __DEF_UC_CONFIG_MIDDLE_PATH="config/uniconfig/frinx/uniconfig"

    # prepare uniconfig cache folder and files
    mkdir -p "${__FOLDER_PATH}/${__CONFIG_PATH}/${__UNICONFIG_SERVICE_SUFIX}/cache"
    chmod -R 777 "${__FOLDER_PATH}/${__CONFIG_PATH}/${__UNICONFIG_SERVICE_SUFIX}/cache"
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

    # swarm node deployment
    sed -i '/&placement-controller$/{n;n;n; s/node.role == manager/uc_deployment/}' ${__COMPOSE_PATH}
    sed -i '/&placement-postgres$/{n;n;n; s/node.role == manager/ucp_deployment/}' ${__COMPOSE_PATH}
    sed -i "s/uc_deployment/${deployment}/g" "${__COMPOSE_PATH}"
    sed -i "s/ucp_deployment/${deployment_psql}/g" "${__COMPOSE_PATH}"

    # swarm config paths
    sed -i 's|${UC_CONFIG_PATH}|'"/${__CONFIG_PATH}/${__UNICONFIG_SERVICE_SUFIX}|g" "${__COMPOSE_PATH}"

    # swarm persistant volume paths
    sed -i "s/uniconfig-postgresql_data/${__SERVICE_NAME}-postgresql_data/g" "${__COMPOSE_PATH}"

    # swarm uniconfig-controller replicas
    sed -i 's|replicas: ${UC_CONTROLLER_REPLICAS:-1}|'"replicas: ${__UC_INSTANCES}|g" "${__COMPOSE_PATH}"

    # labels
    sed -i 's|entrypoints=uniconfig|'"entrypoints=${__SERVICE_NAME/_/-}|g" "${__COMPOSE_PATH}"
    sed -i 's|\.uniconfig\.|'"\.${__SERVICE_NAME}\.|g" "${__COMPOSE_PATH}"

    # env
    sed -i 's|_host=uniconfig-postgres|'"_host=${__SERVICE_NAME}-postgres|g" "${__COMPOSE_PATH}"
    sed -i 's|TRAEFIK_ENTRYPOINTS_UNICONFIG|'"TRAEFIK_ENTRYPOINTS_${__SERVICE_NAME/_/-}|g" "${__COMPOSE_PATH}"

    # networks
    sed -i 's|uniconfig-network|'"${__SERVICE_NAME}-network|g" "${__COMPOSE_PATH}"

}

function prepareFolder {
    if [ -d ${__FOLDER_PATH} ]; then
        rm -rf "${__FOLDER_PATH}/swarm-uniconfig.yml" "${__FOLDER_PATH}/opt"
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
SWARM_STATUS=${ERROR}

FM_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
FM_COMPOSE_DIR="${FM_DIR}/composefiles"

__SERVICE_NAME="uniconfig-controller"
__FOLDER_PATH="${FM_COMPOSE_DIR}/uniconfig"

__UC_COMPOSE_NAME="swarm-uniconfig.yml"

__DEF_CONFIG_PATH="opt/frinx"

__FORCE_GENERATE='false'
__UC_INSTANCES=2
__UNICONFIG_SERVICE_SUFIX="uniconfig-controller"

argumentsCheck "$@"
isNodeInSwarm ${__NODE_ID}
prepareFolder
generateUcCompose
