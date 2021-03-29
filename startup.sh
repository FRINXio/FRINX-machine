#!/bin/bash
# set -e

# Common functions
function example {
    echo -e "example: $scriptName"
}


function usage {
 echo -e "usage: $scriptName [OPTION]\n"
 echo -e "If no options are specified, starts UniFlow and UniConfig services on local node."
 echo -e "To only start UniFlow services locally, use --uniflow-only option."
 echo -e "To deploy UniConfig to a swarm worker node, use --deploy-uniconfig option."
 echo -e "If you do not wish to use the default UniConfig 30 day trial license, change
the license key in $licenseKeyFile before running this script.\n"
 echo -e "To start without micros container use --no-micros. For local and uniflow deployment"
 echo -e ""
}


function show_help {
  usage
    echo -e "OPTIONS:\n"
    echo -e "  --no-micros \t\t\t Deploy Frinx-Machine without uniflow-micros service"
    echo -e "  --https \t\t\t Deploy Frinx-Machine without in https mode"
    echo -e "  --uniflow-only \t\t Deploy UniFlow services locally\n"
    echo -e "  --deploy-uniconfig \t Deploy UniConfig services on swarm worker node \n"
    echo -e "  -h | --help \t\t\t Display this message and exit\n"
  example
}


function argumentsCheck {

  # Default start values
  startupType="local"
  nodeName=$(docker node ls --filter role=manager --format {{.Hostname}})
  noMicros="false"

  export KRAKEND_HTTPS="false"
  export KRAKEND_TLS_PROTOCOL="http"
  export KRAKEND_PORT=80

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

        --uniflow-only|--deploy-uniconfig)
            if [ -z ${__only_one_config} ]; then
              if [ ${1} == "--uniflow-only" ]; then
                __only_one_config="true"
                startupType="uniflow"
              elif [ ${1} == "--deploy-uniconfig" ]; then
                __only_one_config="true";
                startupType="uniconfig"
              fi
            else 
                echo -e "Conflict parameters: --uniflow-only|--deploy-uniconfig !!! Just one can be selected !!!"
                echo -e "Use '${scriptName} --help' for more details"
                exit 1
            fi;;

        -d|--debug) 
            set -x;;

        *) 
            echo "Unknow option: ${1}"
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
  checkSwarmMode
  # load env file
  setVariableEnvFile

  case $startupType in
      uniflow)
      
        export CONSTRAINT_HOSTNAME=${nodeName}

        echo -e "${INFO} Preparing Uniconfig files for multinode deployment"
        isNodeInSwarm "${UNICONFIG_HOSTNAME}"
        checkUniconfigServiceName "${UNICONFIG_SERVICENAME}"
        generateUniconfigComposeFile "${UNICONFIG_HOSTNAME}" "${UNICONFIG_SERVICENAME}"
        generateUniconfigKrakendFile "${UNICONFIG_SERVICENAME}"

        echo -e "${INFO} Uniconfig worker node: ${UNICONFIG_HOSTNAME}"
        echo -e "${INFO} Starting UniFlow on local node ${CONSTRAINT_HOSTNAME}"
        startUniflow
      ;;

      uniconfig)

        export LICENSE=$(cat $licenseKeyFile)

        echo -e "${INFO} Verifying Uniconfig settings for multinode deployment"
        isNodeInSwarm "${UNICONFIG_HOSTNAME}"
        checkUniconfigServiceName "${UNICONFIG_SERVICENAME}"
        checkUniconfigFiles "${UNICONFIG_SERVICENAME}"

        echo -e "${INFO} Deploying UniConfig with license:\n${LICENSE}"
        echo -e "${INFO} Starting UniConfig on worker node ${UNICONFIG_HOSTNAME}"
        echo -e "${INFO} Make sure the UniConfig configuration files are present on remote node in ${UC_CONFIG_PATH} folder"

        docker stack deploy --compose-file "${uniconfigServiceFilesPath}/${dockerSwarmUniconfig}.${UNICONFIG_SERVICENAME}" $stackName
      ;;

      local)

        export CONSTRAINT_HOSTNAME="${nodeName}"
        export LICENSE=$(cat $licenseKeyFile)

        # change env variabled for single-node deployment
        export UNICONFIG_HOSTNAME="${nodeName}" 
        export UNICONFIG_SERVICENAME="${UNICONFIG_HOSTNAME,,}_uniconfig"

        checkUniconfigServiceName "${UNICONFIG_SERVICENAME}"
        generateUniconfigComposeFile "${nodeName}" "${UNICONFIG_SERVICENAME}"
        generateUniconfigKrakendFile "${UNICONFIG_SERVICENAME}"

        echo -e "${INFO} Deploying UniConfig with license:\n${LICENSE}"
        echo -e "${INFO} Swarm node: ${nodeName}"
        echo -e "${INFO} Starting UniFlow and UniConfig services locally"

        startUniflow

        docker stack deploy --compose-file $uniconfigServiceFilesPath/$dockerSwarmUniconfig'.'${UNICONFIG_SERVICENAME} $stackName
      ;;

      *)
        echo -e "${ERROR} This should not happen, exiting..."
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
    echo -e "${ERROR} Change UNICONFIG_HOSTNAME variable in .env file or add node to swarm!"
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


function checkUniconfigServiceName {
  local __service_name="${1}"
  local regex='^[a-z0-9_-]*$'
  echo -e "${INFO} Verify Uniconfig service name: ${__service_name}"
  if [[ "${__service_name}" =~ ${regex} ]]; then
    echo -e "${OK} Uniconfig service name: ${__service_name}"
  else
    echo -e "${ERROR} Uniconfig service name '${__service_name}' contain illegal characters"
    echo -e "${ERROR} Change UNICONFIG_SERVICENAME setting in .env file!!!"
    exit 1
  fi
}


function generateUniconfigComposeFile {
  local __node_name=${1}
  local __service_name=${2}
  
  sed "s/TEMPLATE-SERVICENAME/$__service_name/g;s/TEMPLATE-HOSTNAME/$__node_name/g" composefiles/$dockerSwarmUniconfig | \
    grep -v '#' > $uniconfigServiceFilesPath/$dockerSwarmUniconfig'.'$__service_name
}


function generateUniconfigKrakendFile {

  local __service_name=${1}
  mkdir -p ${krakendUniconfigNode}

cat << EOF > "${krakendUniconfigNodeFile}"
"host": [
  "https://${__service_name}:8181"
]
EOF
}

function checkUniconfigFiles {
  local __service_name="${1}"
  if [[ ! -f "${uniconfigServiceFilesPath}/${dockerSwarmUniconfig}.${__service_name}" ]]; then
    echo -e "${ERROR} Uniconfig compose file is not created, first run --uniflow-only"
    exit 1
  fi
  if [[ ! -f "${krakendUniconfigNodeFile}" ]]; then
    echo -e "${ERROR} KrakendD config file with Uniconfig host name is not created, first run --uniflow-only"
    exit 1
  fi
  grep -q "${__service_name}" "${krakendUniconfigNodeFile}" || \
    ( echo -e "${ERROR} KrakendD config file with Uniconfig host name is not created, first run --uniflow-only" && \
    exit 1 )
}


function createEnvFile {
  if [[ ! -f ${stackEnvFile} ]]; then
    touch ${stackEnvFile} 
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


function setVariableEnvFile {
  if [[ -f ${stackEnvFile} ]]; then
    source ${stackEnvFile}
    local __name=$(grep ^[a-Z] ${stackEnvFile})
    for ((i=0; i< ${#__name[@]}; i++ ))
    do
      export $(echo "${__name[$i]}" | cut -d '=' -f1)
    done
  fi
}


function unsetVariableEnvFile {
  if [[ -f ${stackEnvFile} ]]; then
    local __name=$(grep ^[a-Z] ${stackEnvFile})
    for ((i=0; i< ${#__name[@]}; i++ ))
    do
      unset $(echo "${__name[$i]}" | cut -d '=' -f1)
    done
  fi
}

# =======================================
# Program starts here
# =======================================
scriptName=$0
export FM_DIR="$(dirname "$(readlink -f "${scriptName}")")"

stackName="fm"
stackEnvFile="${FM_DIR}/.env"

licenseKeyFile='./config/uniconfig/uniconfig_license.txt'
dockerSwarmUniconfig='swarm-uniconfig.yml'
dockerSwarmUniflow='swarm-uniflow.yml'
dokcerSwarmKrakend='swarm-uniflow-krakend.yml'
dockerSwarmMicros='swarm-uniflow-micros.yml'
uniconfigServiceFilesPath='composefiles/uniconfig'

krakendUniconfigNode='./config/krakend/partials/uniconfig_host'
krakendUniconfigNodeFile="${krakendUniconfigNode}/host.txt"
ERROR='\033[0;31m[ERROR]:\033[0;0m'
WARNING='\033[0;33m[WARNING]:\033[0;0m'
INFO='\033[0;96m[INFO]:\033[0;0m'
OK='\033[0;92m[OK]:\033[0;0m'

cd ${FM_DIR}

createEnvFile
argumentsCheck "$@"


if [ "${startupType}" = "local" ]; then
  addEnvToFile "UC_CONFIG_PATH" "'${FM_DIR}/config/uniconfig/frinx/uniconfig'"
else
  addEnvToFile "UC_CONFIG_PATH" '"/opt/frinx/uniconfig"'
fi

export UF_CONFIG_PATH="${FM_DIR}/config"

startContainers

echo -e "${INFO} Startup finished"
echo -e "================================================================================"
echo
echo -e "Use 'docker service ls' to check status of services."
echo -e "Each service has REPLICAS 1/1 when everything works (it may take several minutes to start all services)."
echo
echo -e "Use './teardown.sh' to stop all services"
echo -e "or  './teardown.sh -v' to remove also old data if needed."
echo
