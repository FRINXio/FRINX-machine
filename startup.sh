#!/bin/bash
# set -e

. constants.sh

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
    echo -e "  --deploy-uniconfig <hostname>\t Deploy UniConfig services on swarm worker node \n"
    echo -e "  -h | --help \t\t\t Display this message and exit\n"
  example
}


function argumentsCheck {

  # Default start values
  startupType="local"
  nodeName=$(hostname)
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
                if [[ ${2} == "-"* ]] || [[ -z ${2} ]]; then
                  echo -e "Option --deploy-uniconfig requires a hostname \nUse '${scriptName} --help' for more details"
                  exit 1
                else
                  __only_one_config="true";
                  startupType="uniconfig"
                  nodeName=${2}
                fi
                shift;
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

        generateUniconfigKrakendFile
        generateUniconfigComposeFile
        env $(cat ${DIR}/.env | grep ^[A-Z] | xargs) \
        docker stack deploy --compose-file $uniconfigServiceFilesPath/$dockerSwarmUniconfig'.'$nodeName $stackName
      ;;

      local)
        export CONSTRAINT_HOSTNAME=$nodeName
        export LICENSE=$(cat $licenseKeyFile)

        echo -e "${INFO} Deploying UniConfig with license:"
        echo -e "$LICENSE"

        generateUniconfigKrakendFile
        generateUniconfigComposeFile

        echo -e "${INFO} Starting UniFlow and UniConfig services locally"
        startUniflow
        env $(cat ${DIR}/.env | grep ^[A-Z] | xargs) \
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

function generateUniconfigKrakendFile {
mkdir -p ${krakendUnicnfigNode}
cat << EOF > "${krakendUnicnfigNode}/host.txt"
"host": [
  "https://${nodeName}_uniconfig:8181"
]
EOF
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
dokcerSwarmKrakend='swarm-uniflow-krakend.yml'
dockerSwarmMicros='swarm-uniflow-micros.yml'
uniconfigServiceFilesPath='composefiles/uniconfig'
scriptName=$0

krakendUnicnfigNode='./config/krakend/partials/uniconfig_host/'

ERROR='\033[0;31m[ERROR]:\033[0;0m'
WARNING='\033[0;33m[WARNING]:\033[0;0m'
INFO='\033[0;96m[INFO]:\033[0;0m'
OK='\033[0;92m[OK]:\033[0;0m'

DIR="$(dirname "$(readlink -f "${scriptName}")")"
cd ${DIR}

argumentsCheck $@

if [ "$startupType" = "local" ]; then
  export UC_CONFIG_PATH="$DIR/config/uniconfig/frinx/uniconfig"
else
  export UC_CONFIG_PATH='/opt/frinx/uniconfig'
fi

export UF_CONFIG_PATH="$DIR/config"
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
