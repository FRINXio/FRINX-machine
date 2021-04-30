#!/bin/bash
set -e

# Common functions
function example {
  echo -e "example: $scriptName"
}

function show_help() {
cat << EOF
DESCRIPTION:

  USAGE: ${scriptName} [OPTIONS]
  
  Prepares the environment for UniFlow and UniConfig deployment.

  INSTALL CONFIGURATION

    --no-swarm      
          Installer will NOT setup docker swarm during the installation.
          Useful in cases where you don't want to use default swarm
          configuration and want to setup the swarm on you own.
          NOTE: You NEED a working swarm prior to running startup.sh

  DOCKER PROXY CONFIGURATION

    --proxy-conf [path] - path to USER_HOME_DIR/.docker/config.json
          Installer enable configuration of proxy server for docker usage.
          This option create config file in the home directory of the user 
          which starts containers. 
          More info - https://docs.docker.com/network/proxy/
          NOTE: Must be defined PATH or PATH/config.json as argument!!!

    --http-proxy  [ip-address:port] - example "http://127.0.0.1:3001"
                                    - only one PROXY can be used     
                                    - port must be defined
    --https-proxy [ip-address:port] - example "http.example2.com:8123" 
                                    - only one PROXY can be used
                                    - port must be defined
    --no-proxy    [ip-address]      - example "https.test.example.com,127.0.0.1:3002"
                                    - Multiple proxy can be used        
                                    - port can be defined

  COMMON SETTINGS

    -h|--help     Print help
    -d|--debug    Enable verbose

EOF
}

function proxy_config {

if [ -z ${__HTTP_PROXY} ] && [ -z ${__HTTPS_PROXY} ] && [ -z ${__NO_PROXY} ]; then
  __CURRENT_HTTP_PROXY=$(cat ${stackEnvFile} | grep UC_PROXY_HTTP_ENV=) && \
  echo -e ${INFO} "HTTP proxy env settings:" ${__CURRENT_HTTP_PROXY} || true
  __CURRENT_HTTPS_PROXY=$(cat ${stackEnvFile} | grep UC_PROXY_HTTPS_ENV=) && \
  echo -e ${INFO} "HTTPS proxy env settings:" ${__CURRENT_HTTPS_PROXY} || true
  if [ -n "${__CURRENT_HTTP_PROXY}" ] && [ -n "${__CURRENT_HTTPS_PROXY}" ]; then
    echo -e ${WARNING} "Previous proxy configuration was found. For more info see help!"
  fi
 return
else
  if [ -z ${__PROXY_PATH} ]; then
    echo -e ${ERROR} "Missing argument --proxy-conf ${1} \nSee '${scriptName} --help'"
    exit 1
  fi
fi

if [[ -d ${__PROXY_PATH} ]]; then
  __PROXY_FILE="config.json"
  __PROXY_PATH=$(readlink -f "${__PROXY_PATH}")
elif [[ -f ${__PROXY_PATH} ]]; then
  __PROXY_FILE="$(basename ${__PROXY_PATH})"
  __PROXY_PATH=$(dirname $(readlink -f "${__PROXY_PATH}"))
else
    echo -e ${ERROR} "The --proxy-conf value $__PROXY_PATH is not valid"
    exit 1
fi

if [ ! -d ${__PROXY_PATH} ]; then
  install -d -o ${defUser} -m 755 ${__PROXY_PATH} 
  if [ $? -ne 0 ] || [ ! -d ${__PROXY_PATH} ] ; then
    echo -e ${ERROR} "Problem during creating director ${${__PROXY_PATH}}"
    exit 1
  fi
fi

#TODO before create config check count of defined proxy for HTTP and HTTPS
cat << EOF > "${__PROXY_PATH}/${__PROXY_FILE}"
{
  "proxies":
  {
    "default":
    {
      "httpProxy": "${__HTTP_PROXY}",
      "httpsProxy": "${__HTTPS_PROXY}",
      "noProxy": "${__NO_PROXY}"
    }
  }
}
EOF

chown ${defUser}:${defUser} ${__PROXY_PATH}/${__PROXY_FILE}

if [ $? -ne 0 ] || [ ! -f ${__PROXY_PATH}/${__PROXY_FILE} ] ; then
  echo -e ${ERROR} "Problem during creating config file ${__PROXY_PATH}/${__PROXY_FILE}"
  exit 1
elif [ -f ${__PROXY_FILE} ]; then
  echo -e ${INFO} "Proxy configuration file stored in ${__PROXY_PATH}/${__PROXY_FILE}"
fi

if [ -n ${__HTTP_PROXY} ] && [ "${__HTTP_PROXY}" != '' ]; then
  unset __HTTP_PORT
  unset __HTTP_HOST
  IFS=',' read -r -a array <<< "${__HTTP_PROXY}"
  for (( i=0; i< 1; ++i ))
  do
    if [[ "${array[i]}" == "http"* ]] && [[ $(echo "${array[i]}" | tr -d -c ":" | wc -m) -eq 2 ]]; then
      __HTTP_PORT="${__HTTP_PORT}$(echo "${array[i]}"| cut -d ':' -f 3)|"
      __HTTP_HOST="${__HTTP_HOST}$(echo "${array[i]}"| cut -d ':' -f 1,2)|"
    elif [[ "${array[i]}" =~ ^[[:digit:]] ]] && [[ $(echo "${array[i]}" | tr -d -c ":" | wc -m) -eq 1 ]]; then
      __HTTP_PORT="${__HTTP_PORT}$(echo "${array[i]}"| cut -d ':' -f 2)|"
      __HTTP_HOST="${__HTTP_HOST}$(echo "${array[i]}"| cut -d ':' -f 1)|"
    else
      echo -e ${ERROR} "Used bad HTTP Proxy format ${array[i]}"
      exit 1
    fi
  done
  addEnvToFile "UC_PROXY_HTTP_ENV" "'-Dhttp.proxyHost=${__HTTP_HOST%?}'"
  addEnvToFile "UC_PROXY_HTTP_PORT_ENV" "'-Dhttp.proxyPort=${__HTTP_PORT%?}'"
  echo -e ${INFO} "HTTP proxy env settins:" $(cat ${stackEnvFile} | grep "UC_PROXY_HTTP_ENV=\|UC_PROXY_HTTP_PORT_ENV=")
fi

if [ -n ${__HTTPS_PROXY} ] && [ "${__HTTPS_PROXY}" != '' ]; then
  unset __HTTPS_PORT
  unset __HTTPS_HOST

  IFS=',' read -r -a array <<< "${__HTTPS_PROXY}"
  for (( i=0; i< 1; ++i ))
  do
    if [[ "${array[i]}" == "http"* ]] && [[ $(echo "${array[i]}" | tr -d -c ":" | wc -m) -eq 2 ]]; then
      __HTTPS_PORT="${__HTTPS_PORT}$(echo "${array[i]}"| cut -d ':' -f 3),"
      __HTTPS_HOST="${__HTTPS_HOST}$(echo "${array[i]}"| cut -d ':' -f 1,2),"
    elif [[ "${array[i]}" =~ ^[[:digit:]] ]] && [[ $(echo "${array[i]}" | tr -d -c ":" | wc -m) -eq 1 ]]; then
      __HTTPS_PORT="${__HTTPS_PORT}$(echo "${array[i]}"| cut -d ':' -f 2),"
      __HTTPS_HOST="${__HTTPS_HOST}$(echo "${array[i]}"| cut -d ':' -f 1),"
      else
      echo -e ${ERROR} "Used bad HTTP Proxy format ${array[i]}"
      exit 1
    fi
  done
  addEnvToFile "UC_PROXY_HTTPS_ENV" "'-Dhttps.proxyHost=${__HTTPS_HOST%?}'"
  addEnvToFile "UC_PROXY_HTTPS_PORT_ENV" "'-Dhttps.proxyPort=${__HTTPS_PORT%?}'"
  echo -e ${INFO} "HTTPS proxy env settins:" $(cat ${stackEnvFile} | grep "UC_PROXY_HTTPS_ENV=\|UC_PROXY_HTTPS_PORT_ENV=")
fi

if [ -n ${__NO_PROXY} ] && [ "${__NO_PROXY}" != '' ]; then
  unset __NO_HOSTS
  IFS=',' read -r -a array <<< "${__NO_PROXY}"
  for (( i=0; i< "${#array[@]}"; ++i ))
  do
   __NO_HOSTS="${__NO_HOSTS}$(echo "${array[i]}")|"
  done
  addEnvToFile "UC_PROXY_NOPROXY_ENV" "'-Dhttp.nonProxyHosts=${__NO_HOSTS%?}'"
  echo -e ${INFO} "NO proxy env settins:" $(cat ${stackEnvFile} | grep UC_PROXY_NOPROXY_ENV=) 
fi

}

function argumentsCheck {
while [ $# -gt 0 ]
do
    case "${1}" in
        -h|--help) 
            show_help
            exit 0;;
        
        --no-swarm)
            echo -e "${WARNING} Skipping swarm setup"
            echo -e "${WARNING} Please setup the swarm manually prior to running startup.sh" 
            __NO_SWARM="true";;
        --proxy-conf)
            if [[ ${2} != "-"* ]] && [[ ! -z ${2} ]]; then
                __PROXY_PATH="${2}"; shift
            fi;;
        --http-proxy)
            if [[ ${2} != "-"* ]] && [[ ! -z ${2} ]]; then
                __HTTP_PROXY="${2}"; shift
            fi;;
        --https-proxy)
            if [[ ${2} != "-"* ]] && [[ ! -z ${2} ]]; then
                __HTTPS_PROXY="${2}"; shift
            fi;;
        --no-proxy)
            if [[ ${2} != "-"* ]] && [[ ! -z ${2} ]]; then
                __NO_PROXY="${2}"; shift
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


function installPrerequisities {
  echo -e "${INFO} Configuring docker-ce and docker-compose"
  echo -e "${INFO} Checking curl"
  apt-get update -qq
  apt-get install curl -qq -y

  if test -f /usr/bin/dockerd; then
    dockerdVersion=$(/usr/bin/dockerd --version)
    echo -e "${INFO} $dockerdVersion already installed, skipping..."
  else
    echo -e "${INFO} Installing docker-ce"
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    apt-get install software-properties-common
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    apt-get update -qq
    apt-get install -qq -y $dockerInstallVersion

    if [ $skipswarm -eq 0 ]; then
      echo -e "${INFO} Initializing docker in swarm mode"
      docker swarm init
    fi
  fi

  if test -f /usr/local/bin/docker-compose; then
    dockerComposeVersion=$(/usr/local/bin/docker-compose --version)
    echo -e "${INFO} $dockerComposeVersion already installed, skipping..."
  else
    echo -e "${INFO} Installing docker-compose"
    curl -sS -L "https://github.com/docker/compose/releases/download/$dockerComposeInstallVersion/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
  fi
}


function pullImages {

  setVariableFile "${dockerPerformSettings}"

  echo -e "${INFO} Pulling UniFlow images"
  docker-compose --log-level ERROR -f $dockerComposeFileUniflow pull
  docker-compose --log-level ERROR -f $dockerComposeFileMicros pull
  echo -e "${INFO} Pulling UniConfig images"
  docker-compose --log-level ERROR -f $dockerComposeFileUniconfig pull
}


function cleanup {
  echo -e "${INFO} Cleanup"
  docker system prune -f > /dev/null
}

function buildKrakendImage {
  echo -e "${INFO} Building krakend image"
  docker build -t frinx/krakend:$LOCAL_KRAKEND_IMAGE_TAG ./krakend
}


function finishedMessage {
  echo -e "================================================================================"
  echo -e "Installation complete"
  echo
  echo -e "Continue by running ./startup.sh"

  if [ $skipswarm -eq 1 ]
  then
    swarmNote
  fi

  if [ $dockerNoteEnabled -eq 1 ]
  then
    dockerNote
  fi
}


function dockerNote {
  echo -e "Current user has been added to the docker group"
  echo -e "However, for the user to be able to use docker commands, you must logout/login,"
  echo -e "reboot or run 'newgrp docker' command before running ./startup.sh"
  echo ""
}


function swarmNote {
  echo -e "NOTE: Docker swarm not configured!"
  echo -e "Please setup the swarm manually prior to running startup.sh"
  echo ""
}


function checkDockerGroup {
  if [ -z "$(groups $SUDO_USER | grep docker)" ]
  then
    dockerNoteEnabled=1
    echo -e "${INFO} Adding $SUDO_USER to group 'docker'"
    usermod -aG docker $SUDO_USER
  else
    dockerNoteEnabled=0
    echo -e "${INFO} User $SUDO_USER already in group 'docker'"
  fi
}


function checkIfRoot {
  if [ "$EUID" -ne 0 ]
  then
    echo -e "${ERROR} Please re-run as root"
    exit
  fi
}


function selectDockerVersion {
  dockerInstallVersion="docker-ce=5:18.09.9~3-0~ubuntu-bionic"
  ubuntuVersion=$(grep "VERSION_ID" /etc/os-release | cut -d '=' -f2 | sed  's\"\\g')
  if [[ "${ubuntuVersion}" == "20."* ]]; then
    dockerInstallVersion="docker-ce=5:20.10.5~3-0~ubuntu-focal"
  fi
}


function createEnvFile {
  if [[ ! -f ${stackEnvFile} ]]; then
    cp "${DIR}/env.template" ${stackEnvFile}
    chown ${defUser}:${defUser} ${stackEnvFile}
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
      chown ${defUser} ${stackEnvFile}
    else
      echo "${1}=${2}" >> ${stackEnvFile}
      chown ${defUser} ${stackEnvFile}
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


function unsetVariableFile {
  local __filePath="${1}"
  if [[ -f ${__filePath} ]]; then
    local __name=$(grep ^[[:alpha:]] ${__filePath})
    for ((i=0; i< ${#__name[@]}; i++ ))
    do
      unset $(echo "${__name[$i]}" | cut -d '=' -f1)
    done
  fi
}

# =======================================
# Program starts here
# =======================================
selectDockerVersion
dockerComposeInstallVersion="1.22.0"

dockerComposeFileUniconfig='composefiles/swarm-uniconfig.yml'
dockerComposeFileUniflow='composefiles/swarm-uniflow.yml'
dockerComposeFileMicros='composefiles/swarm-uniflow-micros.yml'
dockerPerformSettings='./config/dev_settings.txt'

scriptName=$0
skipswarm=0

# TODO find better way to obrain username
defUser=$(who | awk 'NR==1{print $1;}')

ERROR='\033[0;31m[ERROR]:\033[0;0m'
WARNING='\033[0;33m[WARNING]:\033[0;0m'
INFO='\033[0;96m[INFO]:\033[0;0m'

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
stackEnvFile="${DIR}/.env"

cd ${DIR}

# Workaround to fix composefile when installing
export KRAKEND_PORT=443

argumentsCheck "$@"
checkIfRoot
createEnvFile
setVariableFile "${stackEnvFile}"
proxy_config
installPrerequisities
checkDockerGroup
pullImages
buildKrakendImage
cleanup
finishedMessage
unsetVariableFile "${stackEnvFile}"
unsetVariableFile "${dockerPerformSettings}"