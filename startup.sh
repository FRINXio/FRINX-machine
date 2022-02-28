#!/bin/bash
# set -e

show_help()
{
local ___script_name="$(basename "${0}")"
cat << EOF
DESCRIPTION:
 This script can be used for starting Frinx-Machine (FM) in specific modes.
  
  - If no options are specified, starts UniFlow and UniConfig services on local single node 
    with development resources allocation and http protocol.

  - For starting FM in multi-node is need to generate uniconfig compose files with script:
    ./generate_uc_compose.sh --service-name <arg> --node-id <arg> --folder-path <arg>
    Then you can use ./startup.sh --multinode for start 
    For more info see './generate_uc_compose.sh -h' or README
                          
  - If you do not wish to use the default UniConfig 30 day trial license, change
    the license key in ${licenseKeyFile} before running this script.

  - To use FM with production resource allocation settings, you can use own settings
    stored in ${productPerformSettingFile} or use predefined. 
    For enabling use --prod option. 
  
  For more info see README

OPTIONS:

 ${___script_name} [OPTIONS]

  FRINX-MACHINE CONFIGURATION

   --https       Deploy Frinx-Machine in https mode 
                  - KrakenD with certificates
                  - https://localhost
  
   --auth        Deploy Frinx-Machine with authorization 

   --prod|--dev|--high  
                  Deploy Frinx-Machine in production or development mode
                  - different allocation of resources
                  - default: production

   --uniflow        Deploy UniFlow services
   --uniconfig      Deploy UniConfig services
   --monitoring     Deploy Monitoring services
   --no-monitoring  Deploy UniFlow and UniConfig services

  MULTI-NODE DEPLOYMENT

   --multinode    <PATH>   Deploy FM in multinode mode
                            - Set path to folder witg Uniconfig compose files
                            - Default ${uniconfigServiceFilesPath}
                            - Uniflow on manager node
                            - Uniconfig on worker nodes
                   
   For more info about multi-node deployment see README
                          
  COMMON SETTINGS

   -h|--help    Print this help and exit
   -d|--debug   Enable verbose

EOF
}


show_last_info()
{
echo -e "${INFO} Startup finished:"
cat << EOF
================================================================================

Use 'docker service ls' to check status of services.
Each service has REPLICAS 1/1 when everything works (it may take several minutes to start all services).

Use './teardown.sh' to stop all services
or  './teardown.sh -v' to remove also old data if needed.

EOF

echo -e "${INFO} USE localhost instead of 127.0.0.1"

}


function argumentsCheck {

  while [ $# -gt 0 ]
  do
    case "${1}" in
        -h|--help) show_help
           exit 0;;
        
        --https)
            export TLS_DISABLED="false"
            export KRAKEND_TLS_PROTOCOL="https"
            export KRAKEND_PORT=443;;

        --auth)
            export AUTH_ENABLED="true";;

        --prod|--dev|--high)
            if [ -z ${__only_one_perf_config} ]; then
              if [ ${1} == "--prod" ]; then
                __only_one_perf_config="true"
                performSettings="${productPerformSettingFile}"
              elif [ ${1} == "--dev" ]; then
                __only_one_perf_config="true";
                performSettings="${devPerformSettingFile}"
              elif [ ${1} == "--high" ]; then
                __only_one_perf_config="true";
                performSettings="${highPerformSettingFile}"
              fi
            else 
                echo -e "Conflict parameters: --prod|--dev|--high !!! Just one can be selected !!!"
                echo -e "Use '${scriptName} --help' for more details"
                exit 1
            fi;;

        --uniflow|--uniconfig|--monitoring|--no-monitoring)
            if [ -z ${__only_one_config} ]; then
              if [ ${1} == "--uniflow" ]; then
                __only_one_config="true"
                startupType="uniflow"
              elif [ ${1} == "--uniconfig" ]; then
                __only_one_config="true"
                startupType="uniconfig"
              elif [ ${1} == "--monitoring" ]; then
                __only_one_config="true"
                startupType="monitoring"
              elif [ ${1} == "--no-monitoring" ]; then
                __only_one_config="true"
                startupType="nomonitoring"
              fi
            else 
                echo -e "Conflict parameters: --uniflow|--uniconfig|--monitoring !!! Just one can be selected !!!"
                echo -e "Use '${scriptName} --help' for more details"
                exit 1
            fi;;
        
        -m|--multinode)
            if [[ ${2} != '-'* ]] || [[ ${2} != '' ]]; then 
              if [[ -d ${2} ]]; then
                __multinode="true";
                # todo check is one or more uc composes exist
                uniconfigServiceFilesPath="${2}"
              else
                  echo -e "${ERROR} Wrong path to folder with uniconfig composefiles: '${2}'"
                  exit 1
              fi; shift
            fi;;

        -d|--debug) 
            set -x;;

        *) 
            echo -e "${ERROR} Unknow option: ${1}. See help!"
            exit 1;;
    esac
    shift
  done
}

function startMonitoring {
  echo -e "${INFO} Monitoring swarm node id: ${UF_SWARM_NODE_ID}"
  export TELEGRAF_GROUP=$(stat -c '%g' /var/run/docker.sock)
  export TELEGRAF_HOTNAME=$(stat -c '%g' /var/run/docker.sock)

  docker stack deploy --compose-file composefiles/$dockerSwarmMetrics $stackName
}

function startUniflow {

  echo -e "${INFO} Uniflow swarm worker node id: ${UF_SWARM_NODE_ID}"
  docker stack deploy --compose-file composefiles/$dockerSwarmUniflow $stackName
  status=$?
  if [[ $status -ne 0 ]]; then
    echo -e "${ERROR} Problem with starting Uniflow."
    echo -e "${ERROR} If 'network frinx-machine not found!', wait a while and start Uniflow again."
    exit 1
  fi
}

function startUniconfig {
  export LICENSE=$(cat $licenseKeyFile)
  echo -e "${INFO} UniConfig license: ${LICENSE}"

  if [[ ${__multinode} == "true" ]]; then
    echo -e "${INFO} Multi-node deployment - compose files are stored on this path: ${uniconfigServiceFilesPath}"
    echo -e "${INFO} Make sure the UniConfig configuration files are present on remote node in /opt/frinx folder"
    shopt -s lastpipe
    find ${uniconfigServiceFilesPath} -iname "swarm-uniconfig.yml" -print0 | \
    while IFS= read -r -d '' compose_name; do 
      echo -e "${INFO} Checking swarm nodes for ${compose_name} uniconfig deployment"
      node_id="$(grep node "${compose_name}" | sed -e 's/^[[:space:]]*//')"
      checkUcSwarmMode "${node_id}"
      docker stack deploy --compose-file ${compose_name} $stackName    
    done
  else
    echo -e "${INFO} Single-node deployment - composefiles/${dockerSwarmUniconfig}"
    echo -e "${INFO} Uniconfig swarm worker node hostname: ${UC_SWARM_NODE_ID}"
    docker stack deploy --compose-file "composefiles/${dockerSwarmUniconfig}" $stackName
  fi
}

function startContainers {

  generateUniconfigKrakendFile
  setNodeIdLocalDeploy
  setManagerIpAddrEnv
  
  case $startupType in
      uniflow)
        echo -e "${INFO} Deploying Uniflow only"
        startUniflow
      ;;

      uniconfig)
        echo -e "${INFO} Deploying UniConfig only"
        startUniconfig
      ;;

      monitoring)
        echo -e "${INFO} Deploying Monitoring services only"
        startMonitoring
      ;;

      nomonitoring)
        echo -e "${INFO} Deploying Uniflow and Uniconfig services only"
        startUniflow
        startUniconfig
      ;;

      full)
        echo -e "${INFO} Deploying Uniflow, Uniconfig and Monitoring services"
        startMonitoring
        startUniflow
        startUniconfig
      ;;

      *)
        echo -e "${ERROR} Unknow option: ${startupType}. See help!"
        exit 1
      ;;
  esac

}


function checkSuccess {
  if [[ $? -ne 0 ]]
  then
    echo -e "${ERROR} System is not healthy. Shutting down..."
    docker stack rm $stackName
    exit 1
  fi
}


function isNodeInSwarm {
  if [ -z "$(docker node ls | grep "${1}")" ]
  then
    echo -e "${ERROR} Node ${1} not in swarm for compose: ${2}!"
    docker swarm join-token worker
    exit 1
  else 
      if [[ ${__multi_uniconfig} == "true" ]]; then
        echo -e "${INFO} Service" ${2} "on swarm node id:" ${1}
      fi
  fi
}


function checkSwarmMode {
    if [ "$(docker info --format '{{.Swarm.LocalNodeState}}')" == "inactive" ]
    then
      echo -e "${ERROR} Docker not in swarm mode! Initialize the swarm first using 'docker swarm init'"
      echo -e "Exiting..."
      exit 1
    else
      echo -e "${INFO} Docker running in swarm mode"
    fi
}


function checkUcSwarmMode {

  local TYPE="$(echo ${1}| cut -d ' ' -f 2)"
  local PLACEMENT_INPUT="$(echo ${1}| cut -d ' ' -f 4)"
  if [[ $PLACEMENT_INPUT != '' ]] && [[ $TYPE != '' ]] ; then

    case $TYPE in
      'node.id')
        __id=$(docker node ls -f id=${PLACEMENT_INPUT} --format {{.ID}})
        if [[ "${__id}" == "${PLACEMENT_INPUT}" ]];then
          __name=$(docker node ls -f id=${PLACEMENT_INPUT} --format {{.Hostname}})
          __status=$(docker node inspect ${__name} --format {{.Status.State}}) 
        else
          __name="node.id=${PLACEMENT_INPUT}"
          __status='not found' 
        fi;;

      'node.hostname')
        __name=$(docker node ls -f name=${PLACEMENT_INPUT} --format {{.Hostname}})
        if [[ "${__name}" == "${PLACEMENT_INPUT}" ]];then
          __status=$(docker node inspect ${__name} --format {{.Status.State}}) 
        else
          __name="node.hostname=${PLACEMENT_INPUT}"
          __status='not found' 
        fi;;

      'node.labels.zone')
        __name=$(docker node ls -f node.label=${PLACEMENT_INPUT} --format {{.Hostname}}) || true
        if [[ "${__name}" != '' ]];then
          __status=$(docker node inspect ${__name} --format {{.Status.State}}) 
        else
          __name="node.label=${PLACEMENT_INPUT}"
          __status='not found' 
        fi;;

      'node.role')
        __name=$(docker node ls -f role=${PLACEMENT_INPUT} --format {{.Hostname}}) || true
        if [[ "${__name}" != '' ]];then
          __name=$(docker node ls -f role=${PLACEMENT_INPUT} --format {{.Hostname}})
          __status=$(docker node inspect ${__name} --format {{.Status.State}}) 
        else
          __name="node.role=${PLACEMENT_INPUT}"
          __status='not found' 
        fi;;
      *)
          echo -e "${ERROR} ${TYPE} is not supported"
          return;;
    esac
    
    if [[ "${__status}" != "ready" ]]; then
      echo -e "${ERROR} Swarm node:  ${__name} - ${__node_id} ${__status:-not exist}"
    elif [[ "${__status}" == "ready" ]]; then
      echo -e "${OK} Swarm node ${__name} with placement type ${TYPE} = ${PLACEMENT_INPUT} is ${__status}"
    fi
  fi

}


function checkSwarmNodeActive {
  local __node_id=${1}
  local __status=$(docker node ls --filter id=${__node_id} --format {{.Status}})
  local __name=$(docker node ls --filter id=${__node_id} --format {{.Hostname}})

  if [[ "${__status}" != "Ready" ]]; then
    echo -e "${ERROR} Swarm node:  ${__name} - ${__node_id} ${__status:-not exist}"
  elif [[ "${__status}" == "Ready" ]]; then
    echo -e "${OK} Swarm node:  ${__name} - ${__node_id} is ${__status}"
  fi
}


function setNodeIdLocalDeploy {
  if [ -z "${__multinode}" ]; then
    export UC_SWARM_NODE_ID="${nodeID}"
  fi
  export UF_SWARM_NODE_ID="${nodeID}"
}


function validateAzureAD {
  if [[ ${AUTH_ENABLED} == "false" ]]; then
    echo -e "${WARNING} For Autorization is used Frinx Fake Token"
  elif [[ ${AUTH_ENABLED} == "true" ]]; then
    echo -e "${WARNING} For Autorization is used Azure Active Directory"
  fi
}

function generateUniconfigKrakendFile {

  if [[ ${__multinode} == "true" ]]; then
    shopt -s lastpipe
    find ${uniconfigServiceFilesPath} -iname "swarm-uniconfig.yml" -print0 | \
    while IFS= read -r -d '' traefik_name; do 
      if [[ -z $name ]]; then
        line_num=$(($(cat ${traefik_name} | grep -n "services:" | cut -d ':' -f 1)+1))
        name="\"$(sed -n ${line_num}p ${traefik_name} | cut -d ':' -f 1 | sed 's/ //g')\"" 
      else
        line_num=$(($(cat ${traefik_name} | grep -n "services:" | cut -d ':' -f 1)+1))
        name="\"$(sed -n ${line_num}p ${traefik_name} | cut -d ':' -f 1 | sed 's/ //g')\",\n\t\t${name}"
      fi
    done
    name=${name}
  else
    name='"uniconfig"'
  fi
  sed "s/\"UNICONFIG-NAME\"/${name}/" ${krakendUniconfigTmplFile} > ${krakendUniconfigFile}
}


function setManagerIpAddrEnv {
  MANAGER_IP_ADDR=$(hostname -I | cut -d ' ' -f 1)
  export MANAGER_IP_ADDR
}


function createEnvFile {
  if [[ ! -f ${stackEnvFile} ]]; then
    cp "${FM_DIR}/env.template" ${stackEnvFile}
  fi
}


function addEnvToFile {
  unset __old_env_var
  unset __new_env_var
  if [[ -f ${stackEnvFile} ]]; then
    if grep -Fq ${1} ${stackEnvFile}
    then
      __old_env_var=$(grep -n ^${1}= ${stackEnvFile} | cut -d':' -f1)
      __new_env_var="${1}=${2}"
      sed -i "${__old_env_var}d"  "${stackEnvFile}"
      __old_env_var=$((__old_env_var-1))
      sed -i "${__old_env_var}a ${__new_env_var}"  "${stackEnvFile}"
    else
      echo "${1}=${2}" >> ${stackEnvFile} 
    fi 
  fi
}


function setVariableFile {
  local __filePath="${1}"
  if [[ -f ${__filePath} ]]; then
    source "${__filePath}"
    local __name=$(grep ^[[:alpha:]] ${__filePath})
    for ((i=0; i< ${#__name[@]}; i++ ))
    do
      export $(echo "${__name[$i]}" | cut -d '=' -f1)
    done
  fi
}


function unsetVariableEnvFile {
  if [[ -f ${stackEnvFile} ]]; then
    local __name=$(grep ^[[:alpha:]] ${stackEnvFile})
    for ((i=0; i< ${#__name[@]}; i++ ))
    do
      unset $(echo "${__name[$i]}" | cut -d '=' -f1)
    done
  fi
}

# =======================================
# Program starts here
# =======================================

# COMMON SETTINGS
scriptName="$(basename "${0}")"

FM_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
stackEnvFile="${FM_DIR}/.env"

ERROR="\033[0;31m[ERROR]:\033[0;0m"
WARNING="\033[0;33m[WARNING]:\033[0;0m"
INFO="\033[0;96m[INFO]:\033[0;0m"
OK="\033[0;92m[OK]:\033[0;0m"

# DEFAULT COMPOSE SETTINGS
stackName="fm"
licenseKeyFile="${FM_DIR}/config/uniconfig/uniconfig_license.txt"

dockerSwarmUniflow='swarm-uniflow.yml'
dockerSwarmUniconfig='swarm-uniconfig.yml'

dockerSwarmMetrics='support/swarm-monitoring.yml'

uniconfigServiceFilesPath="${FM_DIR}/composefiles/uniconfig"

# DEFAULT KRAKEND SETTINGS
krakendUniconfigNode="${FM_DIR}/config/krakend/settings"
krakendUniconfigTmplFile="${krakendUniconfigNode}/uniconfig_settings_template.json"
krakendUniconfigFile="${krakendUniconfigNode}/uniconfig_settings.json"

## Default http 
export TLS_DISABLED="true"
export KRAKEND_TLS_PROTOCOL="http"
export KRAKEND_PORT=80

## Default Auth settings
export AUTH_ENABLED=false

# DEFAULT PERFORM SETTINGS
devPerformSettingFile='./config/dev_settings.txt'
productPerformSettingFile='./config/prod_settings.txt'
highPerformSettingFile='./config/high_settings.txt'
performSettings="${productPerformSettingFile}"

# DEFAULT FM START SETTINGS
startupType="full"
nodeID=$(docker node ls --filter role=manager --format {{.Hostname}})
export UC_CONFIG_PATH="${FM_DIR}/config/uniconfig/frinx/uniconfig"
export UF_CONFIG_PATH="${FM_DIR}/config"

# =======================================
# FM starting
# =======================================

pushd ${FM_DIR} > /dev/null

createEnvFile
argumentsCheck "$@"

checkSwarmMode
echo -e "${INFO} Selected resource configuration: ${performSettings}"

setVariableFile "${performSettings}"  # load performance settings
setVariableFile "${stackEnvFile}"     # load .env settings
validateAzureAD

startContainers
show_last_info
popd > /dev/null
