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

  - For starting FM in multi-node, change value of UC_SWARM_NODE_ID in .env file and use
    --uniflow-only for deploy Uniflow on swarm manager node and
    --deploy-uniconfig for deploy Uniconfig on swarm worker node.

  - If you do not wish to use the default UniConfig 30 day trial license, change
    the license key in ${licenseKeyFile} before running this script.

  - To start without micros container use --no-micros. For local and uniflow deployment

  - To use FM with production resource allocation settings, you can use own settings
    stored in ${productPerformSettingFile} or use predefined. 
    For enabling use --prod option. 
  
  For more info see README

OPTIONS:

 ${___script_name} [OPTIONS]

  FRINX-MACHINE CONFIGURATION

   --no-micros   Deploy Frinx-Machine without uniflow-micros service

   --https       Deploy Frinx-Machine in https mode 
                  - KrakenD with certificates
                  - https://127.0.0.1

   --prod|--dev  Deploy Frinx-Machine in production or development mode
                  - different allocation of resources
                  - default: production

   --uniflow      Deploy UniFlow services
   --uniconfig    Deploy UniConfig services

  MULTI-NODE DEPLOYMENT

   --multinode    Deploy FM in multinode mode
                    - Uniflow on manager node
                    - Uniconfig on worker node
                    
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

        --no-micros)
            noMicros="true";;

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
        
        --multinode)
            export UC_CONFIG_PATH="/opt/frinx/uniconfig"
            __multinode="true";;

        -d|--debug) 
            set -x;;

        *) 
            echo -e "${ERROR} Unknow option: ${1}"
            show_help
            exit 1;;
    esac
    shift
  done
}

function startUniflow {
  if [ "$noMicros" = "true" ]; then
    docker stack deploy --compose-file composefiles/$dockerSwarmUniflow --compose-file composefiles/$dokcerSwarmKrakend $stackName
  else 
    docker stack deploy --compose-file composefiles/$dockerSwarmUniflow --compose-file composefiles/$dockerSwarmMicros --compose-file composefiles/$dokcerSwarmKrakend $stackName
  fi 
}

function startContainers {

  case $startupType in
      uniflow)
        echo -e "${INFO} Deploying Uniflow"
        startUniflow
      ;;

      uniconfig)
        export LICENSE=$(cat $licenseKeyFile)
        echo -e "${INFO} Deploying UniConfig with license:\n${LICENSE}"
        docker stack deploy --compose-file "composefiles/${dockerSwarmUniconfig}" $stackName
      ;;

      full)

        export LICENSE=$(cat $licenseKeyFile)
        echo -e "${INFO} Deploying Uniflow and Uniconfig"
        echo -e "${INFO} Deploying UniConfig with license:\n${LICENSE}"
        startUniflow
        docker stack deploy --compose-file "composefiles/${dockerSwarmUniconfig}" $stackName
      ;;

      *)
            echo -e "${ERROR} Unknow option: ${startupType}"
            show_help
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
  if [ -z "$(docker node ls | grep ${1})" ]
  then
    echo -e "${ERROR} Node ${1} not in swarm!"
    echo -e "${ERROR} Change UC_SWARM_NODE_ID variable in .env file or add node to swarm!"
    docker swarm join-token worker
    exit 1
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


function swarmNode {
  checkSwarmMode
  if [ -z "${__multinode}" ]; then
    export UC_SWARM_NODE_ID="${nodeID}" 
  fi
  isNodeInSwarm "${UC_SWARM_NODE_ID}"
  export UF_SWARM_NODE_ID="${nodeID}"

  echo -e "${INFO} Uniflow swarm worker node id: ${UF_SWARM_NODE_ID}"
  echo -e "${INFO} Uniconfig swarm worker node id: ${UC_SWARM_NODE_ID}"

  if [ -n "${__multinode}" ]; then
    echo -e "${INFO} Make sure the UniConfig configuration files are present on remote node in ${UC_CONFIG_PATH} folder"
  fi
}

# TODO when uniconfig image will be changed to non root
function uniconfigCachePermission {
    # for uniconfig non root user
    chmod a+w "${UC_CONFIG_PATH}/cache"
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

dockerSwarmUniconfig='swarm-uniconfig.yml'
dockerSwarmUniflow='swarm-uniflow.yml'
dokcerSwarmKrakend='swarm-uniflow-krakend.yml'
dockerSwarmMicros='swarm-uniflow-micros.yml'
uniconfigServiceFilesPath='composefiles/uniconfig'

# DEFAULT KRAKEND SETTINGS
krakendUniconfigNode='./config/krakend/partials/uniconfig_host'
krakendUniconfigNodeFile="${krakendUniconfigNode}/host.txt"
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
noMicros="false"
export UC_CONFIG_PATH="${FM_DIR}/config/uniconfig/frinx/uniconfig"
export UF_CONFIG_PATH="${FM_DIR}/config"


# =======================================
# FM starting
# =======================================

pushd ${FM_DIR} > /dev/null

createEnvFile
argumentsCheck "$@"

echo -e "${INFO} Selected resource configuration: ${performSettings}"
setVariableFile "${performSettings}"  # load performance settings
setVariableFile "${stackEnvFile}"     # load .env settings
swarmNode

startContainers
show_last_info
popd > /dev/null
