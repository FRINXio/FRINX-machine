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
                  - https://127.0.0.1

   --prod|--dev  Deploy Frinx-Machine in production or development mode
                  - different allocation of resources
                  - default: production

   --uniflow      Deploy UniFlow services
   --uniconfig    Deploy UniConfig services

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
}


function argumentsCheck {

  while [ $# -gt 0 ]
  do
    case "${1}" in
        -h|--help) show_help
           exit 0;;
        
        --https)
            export KRAKEND_HTTPS="true"
            export KRAKEND_TLS_PROTOCOL="https"
            export KRAKEND_PORT=443;;

        --prod|--dev)
            if [ -z ${__only_one_perf_config} ]; then
              if [ ${1} == "--prod" ]; then
                __only_one_perf_config="true"
                performSettings="${productPerformSettingFile}"
              elif [ ${1} == "--dev" ]; then
                __only_one_perf_config="true";
                performSettings="${devPerformSettingFile}"
              fi
            else 
                echo -e "Conflict parameters: --prod|--dev !!! Just one can be selected !!!"
                echo -e "Use '${scriptName} --help' for more details"
                exit 1
            fi;;

        --uniflow|--uniconfig)
            if [ -z ${__only_one_config} ]; then
              if [ ${1} == "--uniflow" ]; then
                __only_one_config="true"
                startupType="uniflow"
              elif [ ${1} == "--uniconfig" ]; then
                __only_one_config="true";
                startupType="uniconfig"
              fi
            else 
                echo -e "Conflict parameters: --uniflow|--uniconfig !!! Just one can be selected !!!"
                echo -e "Use '${scriptName} --help' for more details"
                exit 1
            fi;;
        
        -m|--multinode)
            if [[ ${2} != '-'* ]] || [[ ${2} != '' ]]; then 
              __multinode="true";
              if [[ -d ${2} ]]; then
                # todo check is one or more uc composes exist
                uniconfigServiceFilesPath="${2}"; shift
              fi
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

function startUniflow {
  setKrakendComposeTag
  echo -e "${INFO} Uniflow swarm worker node id: ${UF_SWARM_NODE_ID}"
  docker stack deploy --compose-file composefiles/$dockerSwarmUniflow --compose-file composefiles/$dokcerSwarmKrakend $stackName
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
    find ${uniconfigServiceFilesPath} -iname "swarm-*.yml" -print0 | \
    while IFS= read -r -d '' compose_name; do 
      echo -e "${INFO} Checking swarm nodes for ${compose_name} uniconfig deployment"
      node_id=($(grep node.id "${compose_name}" | sed -e 's/- node.id//;s/==//;s/^[[:space:]]*//'))
      for node in "${node_id[@]}"
      do 
        checkSwarmNodeActive "${node_id}"
      done
      docker stack deploy --compose-file ${compose_name} $stackName    
    done
  else
    echo -e "${INFO} Single-node deployment - composefiles/${dockerSwarmUniconfig}"
    echo -e "${INFO} Uniconfig swarm worker node id: ${UC_SWARM_NODE_ID}"
    docker stack deploy --compose-file "composefiles/${dockerSwarmUniconfig}" --compose-file "composefiles/${dockerSwarmUniconfigPsql}" --compose-file "composefiles/${dokcerSwarmTraefik}" $stackName
  fi
}

function startContainers {

  generateUniconfigKrakendFile
  setNodeIdLocalDeploy

  case $startupType in
      uniflow)
        echo -e "${INFO} Deploying Uniflow only"
        startUniflow
      ;;

      uniconfig)
        echo -e "${INFO} Deploying UniConfig only"
        startUniconfig
      ;;

      full)
        echo -e "${INFO} Deploying Uniflow and Uniconfig"
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


# TODO when uniconfig image will be changed to non root
function uniconfigMountedVolumePermission {
    # for uniconfig non root user
    chmod a+w "${UC_CONFIG_PATH}/cache"
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
    uniconfigMountedVolumePermission
  fi
  export UF_SWARM_NODE_ID="${nodeID}"
}


function generateUniconfigKrakendFile {

  if [[ ${__multinode} == "true" ]]; then
    shopt -s lastpipe
    find ${uniconfigServiceFilesPath} -iname "swarm-*traefik.yml" -print0 | \
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

function setKrakendComposeTag {
  if [[ ${LOCAL_KRAKEND_IMAGE_TAG} == '' ]]; then
    LOCAL_KRAKEND_IMAGE_TAG=${BASE_KRAKEND_IMAGE_TAG}
    export LOCAL_KRAKEND_IMAGE_TAG
    echo -e "${INFO} KrakenD image tag: ${LOCAL_KRAKEND_IMAGE_TAG}"
  fi
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
FM_DIR="$(dirname "$(readlink -f "${scriptName}")")"
stackEnvFile="${FM_DIR}/.env"

ERROR="\033[0;31m[ERROR]:\033[0;0m"
WARNING="\033[0;33m[WARNING]:\033[0;0m"
INFO="\033[0;96m[INFO]:\033[0;0m"
OK="\033[0;92m[OK]:\033[0;0m"

# DEFAULT COMPOSE SETTINGS
stackName="fm"
licenseKeyFile='./config/uniconfig/uniconfig_license.txt'

dockerSwarmUniflow='swarm-uniflow.yml'
dokcerSwarmKrakend='swarm-uniflow-krakend.yml'
dokcerSwarmTraefik='swarm-uniconfig-traefik.yml'
dockerSwarmUniconfig='swarm-uniconfig.yml'
dockerSwarmUniconfigPsql='swarm-uniconfig-postgres.yml'

uniconfigServiceFilesPath="${FM_DIR}/composefiles/uniconfig"

# DEFAULT KRAKEND SETTINGS
krakendUniconfigNode='./config/krakend/settings'
krakendUniconfigTmplFile="${krakendUniconfigNode}/uniconfig_settings_template.json"
krakendUniconfigFile="${krakendUniconfigNode}/uniconfig_settings.json"
mkdir -p ${FM_DIR}/config/krakend/partials/tls

## Default http 
export KRAKEND_HTTPS="false"    
export KRAKEND_TLS_PROTOCOL="http"
export KRAKEND_PORT=80

# DEFAULT PERFORM SETTINGS
devPerformSettingFile='./config/dev_settings.txt'
productPerformSettingFile='./config/prod_settings.txt'
performSettings="${productPerformSettingFile}"

# DEFAULT FM START SETTINGS
startupType="full"
nodeID=$(docker node ls --filter role=manager --format {{.ID}})
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

startContainers
show_last_info
popd > /dev/null
