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

    --update-secrets      
          Update/create docker secrets for Frinx services from  ./config/certificates
          Default names for KrakenD TLS are:
          - frinx_krakend_tls_cert.pem
          - frinx_krakend_tls_key.pem

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
    -s|--skip     Skip installation of dependencies
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
  # TODO improve notification about previous proxy settings
  # if [ -n "${__CURRENT_HTTP_PROXY}" ] && [ -n "${__CURRENT_HTTPS_PROXY}" ]; then
  #   echo -e ${WARNING} "Previous proxy configuration was found. For more info see help!"
  # fi
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
      
        -s|--skip)
            __SKIP_DEP=true;;
            
        --no-swarm)
            echo -e "${WARNING} Skipping swarm setup"
            echo -e "${WARNING} Please setup the swarm manually prior to running startup.sh" 
            __NO_SWARM="true";;

        --update-secrets)
            echo -e "${WARNING} Updating docker frinx secrets"
            __UPDATE_SECRETS="true";;

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


function checkInstallPrerequisities {
  if [[ "${__SKIP_DEP}" != 'true' ]]; then
    FUNC=$(declare -f installPrerequisities)
    sudo bash -c "$FUNC; installPrerequisities"
  fi
}


function installPrerequisities {
  echo -e "${INFO} Configuring docker-ce and docker-compose"
  echo -e "${INFO} Checking curl"
  apt-get update > /dev/null
  apt-get install curl -y

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

    if [[ "${__NO_SWARM}" == "false" ]]; then
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


function updateDockerSecrets {

  for i in $(ls ${dockerCertSettings} )
  do
    local secret_exist=$(docker secret ls -f name=${i} --format {{.Name}})
    if [[ ${secret_exist} != '' ]]; then
      if [ "${__UPDATE_SECRETS}" == "true" ]; then
        echo -e "${INFO} Docker Secrets: Updating docker secret with name ${i}"
        (docker secret rm "${i}" > /dev/null && echo -e "${INFO} Docker Secrets: Remove old secret ${i}") || \
          (echo -e "${ERROR} Docker Secrets: Problem with removing old docker secrets ${i}" && exit 1)
        (docker secret create "${i}" "${dockerCertSettings}/${i}" > /dev/null && echo -e "${INFO} Docker Secrets: Set new secret ${i}") || \
          (echo -e "${ERROR} Docker Secrets: Problem during updating docker secret ${i}" && exit 1)
      else
        echo -e "${INFO} Docker Secrets: Skipping docker secret update with name ${i}"
      fi
    else
      echo -e "${INFO} Docker Secrets: Creating docker secret with name ${i}"
      docker secret create "${i}" "${dockerCertSettings}/${i}" > /dev/null || echo -e "${ERROR} Docker secret not imported" | exit 1
    fi
  done

}


function pullImages {

  setVariableFile "${dockerPerformSettings}"

  echo -e "${INFO} Pulling UniFlow images"
  docker-compose --log-level ERROR -f $dockerComposeFileUniflow pull
  echo -e "${INFO} Pulling UniConfig images"
  docker-compose --log-level ERROR -f $dockerComposeFileUniconfig pull

  echo -e "${INFO} Pulling Monitoring images"
  docker-compose --log-level ERROR -f $dockerComposeFileMonitor pull

  echo -e "${INFO} Pulling Krakend base image"
  docker pull frinx/krakend:${BASE_KRAKEND_IMAGE_TAG}

}


function cleanup {
  echo -e "${INFO} Cleanup"
  docker system prune -f > /dev/null
}


function finishedMessage {
  echo -e "================================================================================"
  echo -e "Installation complete"
  echo
  echo -e "Continue by running ./startup.sh"

  if [[ $__NO_SWARM == "true" ]]
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


function installLokiPlugin {
  echo -e "${INFO} Checking Loki logging driver plugin"
  docker plugin inspect loki:latest > /dev/null 2>&1 || \
  (docker plugin install grafana/loki-docker-driver:main-20515a2 --alias loki --grant-all-permissions || true)
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



function selectDockerVersion {
  dockerInstallVersion="docker-ce=5:18.09.9~3-0~ubuntu-bionic"
  ubuntuVersion=$(grep "VERSION_ID" /etc/os-release | cut -d '=' -f2 | sed  's\"\\g')
  if [[ "${ubuntuVersion}" == "20."* ]]; then
    dockerInstallVersion="docker-ce=5:20.10.5~3-0~ubuntu-focal"
  fi
}


function createEnvFile {
  if [[ ! -f ${stackEnvFile} ]]; then
    cp "${FM_DIR}/env.template" ${stackEnvFile}
  else
    echo -e "${WARNING} Used ${stackEnvFile} from previous installation!"
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

scriptName="$(basename "${0}")"
FM_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
stackEnvFile="${FM_DIR}/.env"

dockerComposeFileUniconfig="${FM_DIR}/composefiles/swarm-uniconfig.yml"
dockerComposeFileUniflow="${FM_DIR}/composefiles/swarm-uniflow.yml"
dockerComposeFileMonitor="${FM_DIR}/composefiles/support/swarm-monitoring.yml"

dockerPerformSettings="${FM_DIR}/config/dev_settings.txt"
dockerCertSettings="${FM_DIR}/config/certificates"

__NO_SWARM="false"

# TODO find better way to obrain username
defUser=$(who | awk 'NR==1{print $1;}')

ERROR='\033[0;31m[ERROR]:\033[0;0m'
WARNING='\033[0;33m[WARNING]:\033[0;0m'
INFO='\033[0;96m[INFO]:\033[0;0m'

pushd ${FM_DIR} > /dev/null

# Workaround to fix composefile when installing
export KRAKEND_PORT=443

argumentsCheck "$@"
createEnvFile
setVariableFile "${stackEnvFile}"
proxy_config
checkInstallPrerequisities
installLokiPlugin
checkDockerGroup
updateDockerSecrets
pullImages
cleanup
finishedMessage
unsetVariableFile "${stackEnvFile}"
unsetVariableFile "${dockerPerformSettings}"

popd