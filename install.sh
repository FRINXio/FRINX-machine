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
          Default certificate names:
          - frinx_krakend_tls_cert.pem
          - frinx_krakend_tls_key.pem
          - frinx_uniconfig_tls_cert.pem
          - frinx_uniconfig_tls_key.pem

    --custom-ssl-key
          Select custom frinx_krakend_tls_key.pem

    --custom-ssl-cert
          Select custom frinx_krakend_tls_cert.pem

  COMMON SETTINGS
    -i|--install-deps     Installation of dependencies
    -h|--help             Print help
    -d|--debug            Enable verbose

EOF
}

function argumentsCheck {
while [ $# -gt 0 ]
do
    case "${1}" in
        -h|--help) 
            show_help
            exit 0;;
      
        -i|--install-deps)
            __SKIP_DEP="false";;
            
        --no-swarm)
            echo -e "${WARNING} Skipping swarm setup"
            echo -e "${WARNING} Please setup the swarm manually prior to running startup.sh" 
            __NO_SWARM="true";;

        --update-secrets)
            echo -e "${WARNING} Updating docker frinx secrets"
            __UPDATE_SECRETS="true";;

        --custom-ssl-key)
            if [[ -f ${2} ]]; then
              KRAKEND_SSL_KEY_PATH="${2}";
              echo -e "${WARNING} Used custom SSL key"; shift
            else
              echo -e "${ERROR} Bad path ${2} for SSL key"
              exit 1
            fi;;

        --custom-ssl-cert)
            echo -e "${WARNING} Used custom SSL cert"
            if [[ -f ${2} ]]; then
                KRAKEND_SSL_CERT_PATH="${2}"; shift
            else
              echo -e "${ERROR} Bad path ${2} for SSL cert"
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


function checkInstallPrerequisities {
  if [[ "${__SKIP_DEP}" != 'true' ]]; then
    FUNC=$(declare -f installPrerequisities)
    sudo bash -c "$FUNC; installPrerequisities"
  fi
}


function installPrerequisities {
  echo -e "${INFO} Configuring docker-ce"
  echo -e "${INFO} Checking curl"
  apt-get update > /dev/null
  apt-get install curl openssl -y

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
}

function generateUniconfigTLSCerts {

  if ([[ $(docker secret ls --filter name=${UNICONFIG_SSL_KEY} --format {{.Name}}) == '' ]] || [[ $(docker secret ls --filter name=${UNICONFIG_SSL_CERT} --format {{.Name}}) == '' ]]) || [ "${__UPDATE_SECRETS}" == "true" ]; then
    docker secret rm $( docker secret ls -q -f name=${UNICONFIG_SSL_KEY} -f name=${UNICONFIG_SSL_CERT} -f name=${UNICONFIG_SSL_PCKS8} -f name=${UNICONFIG_SSL_PCKS12}) &>/dev/null || true
    if ([[ ! -f "${dockerCertSettings}/${UNICONFIG_SSL_KEY}" ]] || [[ ! -f "${dockerCertSettings}/${UNICONFIG_SSL_CERT}" ]] || [[ ! -f "${dockerCertSettings}/${UNICONFIG_SSL_PCKS8}" ]] || [[ ! -f "${dockerCertSettings}/${UNICONFIG_SSL_PCKS12}" ]]); then
      echo -e "${INFO} Generating SSL key/cert used for uniconfig-zone TLS communication"
      openssl genrsa --out ${dockerCertSettings}/${UNICONFIG_SSL_KEY} &>/dev/null
      openssl req -new -x509 -key ${dockerCertSettings}/${UNICONFIG_SSL_KEY} -out ${dockerCertSettings}/${UNICONFIG_SSL_CERT} -days 365 \
            -subj '/C=SK/ST=Slovakia/L=Bratislava/O=Frinx/OU=Frinx Machine/CN=*/emailAddress=frinx@frinx.io' -addext "subjectAltName = DNS:*"
      openssl pkcs8 -in ${dockerCertSettings}/${UNICONFIG_SSL_KEY} -topk8 -nocrypt -outform DER -out ${dockerCertSettings}/${UNICONFIG_SSL_PCKS8}
      # READ PASSWORD FOR UNICONFIG TLS FROM SECRET FOLDER
      UNICONFIG_SSL_PCKS12_PASS=$(cat ${dockerEnvSettings}/frinx_uniconfig_db | grep dbPersistence_connection_sslPassword | cut -d '=' -f 2)
      openssl pkcs12 -export -name uniconfig -passout pass:${UNICONFIG_SSL_PCKS12_PASS} -out ${dockerCertSettings}/${UNICONFIG_SSL_PCKS12} \
            -inkey ${dockerCertSettings}/${UNICONFIG_SSL_KEY} -in ${dockerCertSettings}/${UNICONFIG_SSL_CERT} -certfile ${dockerCertSettings}/${UNICONFIG_SSL_CERT}
    fi
      echo -e "${INFO} Updating SSL key/cert used for uniconfig-zone TLS communication"
      docker secret create "${UNICONFIG_SSL_KEY}" "${dockerCertSettings}/${UNICONFIG_SSL_KEY}" > /dev/null || echo -e "${ERROR} Docker secret ${UNICONFIG_SSL_KEY} not imported" | exit 1
      docker secret create "${UNICONFIG_SSL_CERT}" "${dockerCertSettings}/${UNICONFIG_SSL_CERT}" > /dev/null || echo -e "${ERROR} Docker secret ${UNICONFIG_SSL_CERT} not imported" | exit 1
      docker secret create "${UNICONFIG_SSL_PCKS8}" "${dockerCertSettings}/${UNICONFIG_SSL_PCKS8}" > /dev/null || echo -e "${ERROR} Docker secret ${UNICONFIG_SSL_PCKS8} not imported" | exit 1
      docker secret create "${UNICONFIG_SSL_PCKS12}" "${dockerCertSettings}/${UNICONFIG_SSL_PCKS12}" > /dev/null || echo -e "${ERROR} Docker secret ${UNICONFIG_SSL_PCKS12} not imported" | exit 1
  fi
}


function generateKrakenDTLSCerts {

  if [[ -f "${KRAKEND_SSL_KEY_PATH}" ]] || [[ -f "${KRAKEND_SSL_CERT_PATH}" ]]; then
    echo -e "${INFO} Validation of key/cert used for KrakenD TLS communication"
    key_md5=$(openssl rsa -modulus -noout -in ${KRAKEND_SSL_KEY_PATH} | openssl md5)
    cert_md5=$(openssl x509 -modulus -noout -in ${KRAKEND_SSL_CERT_PATH} | openssl md5)
    if [[ $key_md5 != $cert_md5 ]]; then
      echo $key_md5 $cert_md5
      echo -e "${ERROR} SSL key ${KRAKEND_SSL_KEY_PATH} is not compatible with cert ${KRAKEND_SSL_CERT_PATH}"
      exit 1
    fi
    echo -e "${INFO} Remove old ${KRAKEND_SSL_KEY} / ${KRAKEND_SSL_CERT} from docker secret"
    docker secret rm $( docker secret ls -q -f name=${KRAKEND_SSL_KEY} -f name=${KRAKEND_SSL_CERT}) &>/dev/null || true
    echo -e "${INFO} Creating new ${KRAKEND_SSL_KEY} / ${KRAKEND_SSL_CERT} to docker secret"
    docker secret create "${KRAKEND_SSL_KEY}" "${KRAKEND_SSL_KEY_PATH}" > /dev/null || echo -e "${ERROR} Docker secret ${KRAKEND_SSL_KEY} not imported" | exit 1
    docker secret create "${KRAKEND_SSL_CERT}" "${KRAKEND_SSL_CERT_PATH}" > /dev/null || echo -e "${ERROR} Docker secret ${KRAKEND_SSL_CERT} not imported" | exit 1
  elif ([[ $(docker secret ls --filter name=${KRAKEND_SSL_KEY} --format {{.Name}}) == '' ]] || [[ $(docker secret ls --filter name=${KRAKEND_SSL_CERT} --format {{.Name}}) == '' ]]) || [ "${__UPDATE_SECRETS}" == "true" ]; then
    docker secret rm $( docker secret ls -q -f name=${KRAKEND_SSL_KEY} -f name=${KRAKEND_SSL_CERT}) &>/dev/null || true
    if [[ ! -f "${dockerCertSettings}/${KRAKEND_SSL_KEY}" ]] || [[ ! -f "${dockerCertSettings}/${KRAKEND_SSL_CERT}" ]]; then
      echo -e "${INFO} Generating SSL key/cert used for KrakenD TLS communication"
      openssl genrsa --out ${dockerCertSettings}/${KRAKEND_SSL_KEY} &>/dev/null
      openssl req -new -x509 -key ${dockerCertSettings}/${KRAKEND_SSL_KEY} -out ${dockerCertSettings}/${KRAKEND_SSL_CERT} -days 365 \
            -subj '/C=SK/ST=Slovakia/L=Bratislava/O=Frinx/OU=Frinx Machine/CN=*/emailAddress=frinx@frinx.io' -addext "subjectAltName = DNS:*"
    fi
    echo -e "${INFO} Updating SSL key/cert used for KrakenD TLS communication"
    docker secret create "${KRAKEND_SSL_KEY}" "${dockerCertSettings}/${KRAKEND_SSL_KEY}" > /dev/null || echo -e "${ERROR} Docker secret ${KRAKEND_SSL_KEY} not imported" | exit 1
    docker secret create "${KRAKEND_SSL_CERT}" "${dockerCertSettings}/${KRAKEND_SSL_CERT}" > /dev/null || echo -e "${ERROR} Docker secret ${KRAKEND_SSL_CERT} not imported" | exit 1
  fi

}


function updateDockerEnvSecrets {

  for i in $(ls ${dockerEnvSettings} )
  do
    local secret_exist=$(docker secret ls -f name=${i} --format {{.Name}})
    if [[ ${secret_exist} != '' ]]; then
      if [ "${__UPDATE_SECRETS}" == "true" ]; then
        echo -e "${INFO} Docker Secrets: Updating docker secret with name ${i}"
        (docker secret rm "${i}" > /dev/null && echo -e "${INFO} Docker Secrets: Remove old secret ${i}") || \
          (echo -e "${ERROR} Docker Secrets: Problem with removing old docker secrets ${i}" && exit 1)
        (docker secret create "${i}" "${dockerEnvSettings}/${i}" > /dev/null && echo -e "${INFO} Docker Secrets: Set new secret ${i}") || \
          (echo -e "${ERROR} Docker Secrets: Problem during updating docker secret ${i}" && exit 1)
      else
        echo -e "${INFO} Docker Secrets: Skipping docker secret update with name ${i}"
      fi
    else
      echo -e "${INFO} Docker Secrets: Creating docker secret with name ${i}"
      docker secret create "${i}" "${dockerEnvSettings}/${i}" > /dev/null || echo -e "${ERROR} Docker secret not imported" | exit 1
    fi
  done

}


function pullImages {

  setVariableFile "${dockerPerformSettings}"

  # Workaround to fix composefile when installing
  export KRAKEND_PORT=443

  echo -e "${INFO} Pulling Monitoring images"
  docker compose -f $dockerComposeFileMonitor --env-file $dockerPerformSettings pull --ignore-pull-failures || true
  echo -e "${INFO} Pulling Uniflow images"
  docker compose -f $dockerComposeFileUniflow --env-file $dockerPerformSettings pull --ignore-pull-failures || true

  echo -e "${INFO} Pulling Uniconfig images"
  docker compose -f $dockerComposeFileUniconfig --env-file $dockerPerformSettings pull --ignore-pull-failures || true

  echo -e "${INFO} Pulling Unistore images"
  docker compose -f $dockerComposeFileUnistore --env-file $dockerPerformSettings pull --ignore-pull-failures || true
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
  # check if the file exists and if contain at least one config parameter
  if [[ -f ${__filePath} ]] && [[ "$(grep -v '^\s*$\|^\s*\#' ${__filePath})" != "" ]]; then
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
  # check if the file exists and if contain at least one config parameter
  if [[ -f ${__filePath} ]] && [[ "$(grep -v '^\s*$\|^\s*\#' ${__filePath})" != "" ]]; then
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

scriptName="$(basename "${0}")"
FM_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
stackEnvFile="${FM_DIR}/.env"

dockerComposeFileUniconfig="${FM_DIR}/composefiles/swarm-uniconfig.yml"
dockerComposeFileUniflow="${FM_DIR}/composefiles/swarm-uniflow.yml"
dockerComposeFileUnistore="${FM_DIR}/composefiles/swarm-unistore.yml"

dockerComposeFileMonitor="${FM_DIR}/composefiles/support/swarm-monitoring.yml"

dockerPerformSettings="${FM_DIR}/config/dev_settings.txt"
dockerCertSettings="${FM_DIR}/config/certificates"
dockerEnvSettings="${FM_DIR}/config/secrets"

UNICONFIG_SSL_KEY="frinx_uniconfig_tls_key.pem"
UNICONFIG_SSL_CERT="frinx_uniconfig_tls_cert.pem"
UNICONFIG_SSL_PCKS8="frinx_uniconfig_tls_key.der"
UNICONFIG_SSL_PCKS12="frinx_uniconfig_tls_key.p12"
KRAKEND_SSL_KEY="frinx_krakend_tls_key.pem"
KRAKEND_SSL_CERT="frinx_krakend_tls_cert.pem"

__NO_SWARM="false"
__SKIP_DEP="true"

# TODO find better way to obrain username
defUser=$(who | awk 'NR==1{print $1;}')

ERROR='\033[0;31m[ERROR]:\033[0;0m'
WARNING='\033[0;33m[WARNING]:\033[0;0m'
INFO='\033[0;96m[INFO]:\033[0;0m'

pushd ${FM_DIR} > /dev/null

  argumentsCheck "$@"
  createEnvFile
  setVariableFile "${stackEnvFile}"
  checkInstallPrerequisities
  installLokiPlugin
  checkDockerGroup
  generateUniconfigTLSCerts
  generateKrakenDTLSCerts
  updateDockerEnvSecrets
  pullImages
  cleanup
  finishedMessage
  unsetVariableFile "${stackEnvFile}"
  unsetVariableFile "${dockerPerformSettings}"

popd > /dev/null
