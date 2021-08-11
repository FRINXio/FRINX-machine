#!/bin/bash

show_help() {
cat << EOF
DESCRIPTION:

 ${__SCRIPT_NAME} [OPTIONS] 

    - Used for building krakend image with uniconfig certificates
    - Default krakend image tag is 'with_certificates'
    - Last tag is stored in .env file and is used in ./startup.sh 

OPTIONS:
    -t|--tag            set krakend image tag (default 'with_certificates')

    -h|--help           print help
    -d|--debug          enable verbose
EOF
}


function argumentsCheck {
while [ $# -gt 0 ]
do
    case "${1}" in
        -h|--help) 
            show_help
            exit 0;;
        
        -t|--tag)
          if [[ ${2} != '' ]]; then
            checkUniconfigServiceName ${2}
            __ENV_LOCAL_KRAKEND_IMAGE_TAG_VALUE="${2}";shift;
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

function buildKrakendImage() {
  echo -e "${INFO} Building krakend image"
  echo ${BASE_KRAKEND_IMAGE_TAG} 
  docker build --build-arg "KRAKEND_TAG=${BASE_KRAKEND_IMAGE_TAG}" -t frinx/krakend:$LOCAL_KRAKEND_IMAGE_TAG ./krakend
}

function checkUniconfigServiceName {
  local __service_name="${1}"
  local regex='^[a-z0-9_.-]*$'
  echo -e "${INFO} Verify KrakenD image tag name: ${__service_name}"
  if [[ "${__service_name}" =~ ${regex} ]]; then
    echo -e "${OK} KrakenD image tag name: ${__service_name}"
  else
    echo -e "${ERROR} KrakenD image tag name '${__service_name}' contain illegal characters"
    exit 1
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

function createEnvFile {
  if [[ ! -f ${stackEnvFile} ]]; then
    cp "${FM_DIR}/env.template" ${stackEnvFile}
  fi
}

# =======================================
# Program starts here
# =======================================

# DEFAULT VARIABLES

__SCRIPT_NAME="$(basename "${0}")"
__SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

__ENV_BASE_KRAKEND_IMAGE_TAG="BASE_KRAKEND_IMAGE_TAG"
__ENV_LOCAL_KRAKEND_IMAGE_TAG="LOCAL_KRAKEND_IMAGE_TAG"
__ENV_LOCAL_KRAKEND_IMAGE_TAG_DEFAULT="with_certificates"
__ENV_LOCAL_KRAKEND_IMAGE_TAG_VALUE=${__ENV_LOCAL_KRAKEND_IMAGE_TAG_DEFAULT}

INFO="\033[0;96m[INFO]:\033[0;0m"
stackEnvFile="${__SCRIPT_PATH}/.env"

pushd ${__SCRIPT_PATH} > /dev/null

createEnvFile
argumentsCheck "$@"
addEnvToFile "${__ENV_LOCAL_KRAKEND_IMAGE_TAG}" "'${__ENV_LOCAL_KRAKEND_IMAGE_TAG_VALUE}'"
setVariableFile "${stackEnvFile}"
buildKrakendImage

popd > /dev/null

