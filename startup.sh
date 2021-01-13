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
the license key in $licenseKeyFile before running this script."
 echo -e ""
 echo -e "To start without micros container use --no-micros. For local and uniflow deployment"
 echo -e ""
}


function help {
  usage
    echo -e "OPTIONS:"
    echo -e " -h | --help                    Display this message and exit"
    echo -e "[--no-micros --http]                   Do not start micros container/ Deploy in http mode"
    echo -e " --uniflow-only [--no-micros --http]   Deploy UniFlow services locally"
    echo -e " --deploy-uniconfig <hostname>  Deploy UniConfig services on swarm worker node"
    echo -e ""
  example
}


function argumentsCheck {

  # Default start values
  startupType="local"
  nodeName=$(hostname)
  noMicros="false"
  API_GATEWAY_HTTPS="true"
  API_GATEWAY_HEALTHCHECK_PROTOCOL="https"
  API_GATEWAY_PORT=443


  case $1 in
    -h|--help)
      help
      exit
    ;;

    --uniflow-only)
      startupType="uniflow"
      shift
      parseAdditionalArgs $@
    ;;

    --deploy-uniconfig)
      if [ -z $2 ]
      then
        echo -e "Option --deploy-uniconfig requires a hostname"
        exit
      else
        startupType="uniconfig"
        nodeName=$3
      fi
    ;;

    *)
      parseAdditionalArgs $@
    ;;
  esac
}

function parseAdditionalArgs {
  until [ -z "$1" ]  # Until all parameters used up . . .
  do
    case $1 in
     --no-micros)
        noMicros="true"
      ;;
     
     --http)
       API_GATEWAY_HTTPS="false"
       API_GATEWAY_HEALTHCHECK_PROTOCOL="http"
       API_GATEWAY_PORT=80
      ;;

      *)
        echo -e "Uknown argument $1, see --help for more info"
        exit
      ;;
    esac
    shift
  done
}

function startUniflow {
  if [ "$noMicros" = "true" ]; then
    docker stack deploy --compose-file composefiles/$dockerSwarmUniflow $stackName
  else 
    docker stack deploy --compose-file composefiles/$dockerSwarmUniflow --compose-file composefiles/$dockerSwarmMicros $stackName
  fi 
}

function startContainers {
  checkSwarmMode

  case $startupType in
      uniflow)
        export CONSTRAINT_HOSTNAME=$nodeName

        echo -e "${INFO} Starting UniFlow on local node $(hostname)"
        startUniflow
      ;;

      uniconfig)
        isNodeInSwarm $nodeName
        export CONSTRAINT_HOSTNAME=$nodeName
        export LICENSE=$(cat $licenseKeyFile)

        echo -e "${INFO} Deploying UniConfig with license:"
        echo -e "$LICENSE"
        echo -e "${INFO} Starting UniConfig on worker node $nodeName"
        echo -e "${INFO} Make sure the UniConfig configuration files are present on remote node in $UC_CONFIG_PATH folder"

        generateUniconfigComposeFile
        docker stack deploy --compose-file $uniconfigServiceFilesPath/$dockerSwarmUniconfig'.'$nodeName $stackName
      ;;

      local)
        export CONSTRAINT_HOSTNAME=$nodeName
        export LICENSE=$(cat $licenseKeyFile)

        echo -e "${INFO} Deploying UniConfig with license:"
        echo -e "$LICENSE"
        generateUniconfigComposeFile

        echo -e "${INFO} Starting UniFlow and UniConfig services locally"
        startUniflow
        docker stack deploy --compose-file $uniconfigServiceFilesPath/$dockerSwarmUniconfig'.'$nodeName $stackName
      ;;

      *)
        echo -e "${ERROR} This should not happen, exiting..."
        exit
      ;;
  esac
}


function checkSuccess {
  if [[ $? -ne 0 ]]
  then
    echo -e "${ERROR} System is not healthy. Shutting down..."
    docker stack rm $stackName
    exit
  fi
}


function isNodeInSwarm {
  if [ -z "$(docker node ls | grep $1)" ]
  then
    echo -e "${ERROR} Node $1 not in swarm!"
    docker swarm join-token worker
    exit
  fi
}


function generateUniconfigComposeFile {
  sed "s/TEMPLATE-HOSTNAME/$nodeName/g" composefiles/$dockerSwarmUniconfig | grep -v '#' > $uniconfigServiceFilesPath/$dockerSwarmUniconfig'.'$nodeName
}


function checkSwarmMode {
    if [ "$(docker info --format '{{.Swarm.LocalNodeState}}')" == "inactive" ]
    then
      echo -e "${ERROR} Docker not in swarm mode! Initialize the swarm first using 'docker swarm init'"
      echo -e "Exiting..."
      exit
    else
      echo -e "${INFO} Docker running in swarm mode"
    fi
}


# =======================================
# Program starts here
# =======================================
stackName="fm"
licenseKeyFile='./config/uniconfig/uniconfig_license.txt'
dockerSwarmUniconfig='swarm-uniconfig.yml'
dockerSwarmUniflow='swarm-uniflow.yml'
dockerSwarmMicros='swarm-uniflow-micros.yml'
uniconfigServiceFilesPath='composefiles/uniconfig'
scriptName=$0

ERROR='\033[0;31m[ERROR]:\033[0;0m'
WARNING='\033[0;33m[WARNING]:\033[0;0m'
INFO='\033[0;96m[INFO]:\033[0;0m'
OK='\033[0;92m[OK]:\033[0;0m'

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

argumentsCheck $@

if [ "$startupType" = "local" ]; then
  export UC_CONFIG_PATH="$DIR/config/uniconfig/frinx/uniconfig"
else
  export UC_CONFIG_PATH='/opt/frinx/uniconfig'
fi

export UF_CONFIG_PATH="$DIR/config"

export API_GATEWAY_HTTPS API_GATEWAY_HEALTHCHECK_PROTOCOL API_GATEWAY_PORT

startContainers

echo -e "${INFO} Startup finished"
echo -e "================================================================================"
echo
echo -e "Use 'docker service ls' to check status of services."
echo -e "Each service has REPLICAS 1/1 when everything works (it may take several minutes to start all services)."
echo
echo -e "Use 'docker stack rm $stackName' to stop all services and"
echo -e "'docker volume prune' to remove old data if needed."
echo
