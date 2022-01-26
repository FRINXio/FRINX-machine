#!/bin/bash

# set env variables from docker secret to service

show_help()
{
local ___script_name="$(basename "${0}")"
cat << EOF
DESCRIPTION:
 Configure Azure AD environment variables in: '${stackEnvFile}' 
  
  - Enable Azure AD authorization in Frinx Machine

  - Transform Tenant ID, replace '-' with '_'

  - Check if all configuration parameters are obtained in .env file
                          
Azure AD environment configuration

  ./${___script_name} configure [OPTIONS] -a -n -i -c -s -r

      -a|--azure_enable    Enable Azure AD authorizathion
                            in Frinx Machine
      
      -n|--tenant_domain     Azure AD Tenant Domain (Primary domain)
                            - sinle-tenant: e.g. yourname.onmicrosoft.com
                            - multi-tenant: "common"

      -i|--tenant_id       Azure AD Tenant ID
                            - e.g. aaaaaaaa_bbbb_cccc_dddd_eeeeeeeeeeee

      -c|--client_id       Application (client) ID
                            - e.g. aaaaaaaa_bbbb_cccc_dddd_eeeeeeeeeeee

      -s|--client_secret   Application Secret
                            - A secret string that the application uses to prove its 
                              identity when requesting a token.
                            - e.g. 79A4Q~RL5pELYji-KU58UfSeGoRVGco8f20~K

      -r|--redirect_url    Single-page application redirect URI
                            - IP which is accesed
                            - e.g. localhost, 10.15.0.7, yourdomain.com
    COMMON SETTINGS

      -h|--help    Print this help and exit
      -d|--debug   Enable verbose

Azure AD environment validation

  ./${___script_name} validation

EOF
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

function validate_id {
  if [[ ${1} =~ ^[a-z0-9]{8}[-_][a-z0-9]{4}[-_][a-z0-9]{4}[-_][a-z0-9]{4}[-_][a-z0-9]{12} ]]; then
    return
  else
    ERROR="\033[0;31m[ERROR]:\033[0;0m"
    echo -e "${ERROR} Bad Tenant or Client ID: ${1}"
    exit 1
  fi
}

function validate {
  setVariableFile "${stackEnvFile}"
  if [ -z ${AZURE_TENANT_ID}  ] ||  [ -z $AZURE_TENANT_NAME  ] || [ -z $AZURE_CLIENT_ID  ]  || [ -z $AZURE_CLIENT_SECRET  ] || [ -z $REDIRECT_URI  ]; then
    ERROR="\033[0;31m[ERROR]:\033[0;0m"
    echo -e "${ERROR} Missing one or multiple AzureAD config parameters in ${stackEnvFile}!"
    exit 1
  fi

  validate_id "${AZURE_TENANT_ID}"
  validate_id "${AZURE_CLIENT_ID}"

  return
}

function configure {
  ERROR="\033[0;31m[ERROR]:\033[0;0m"
  WARNING="\033[0;33m[WARNING]:\033[0;0m"
  INFO="\033[0;96m[INFO]:\033[0;0m"
  OK="\033[0;92m[OK]:\033[0;0m"
  while [ $# -gt 0 ]
  do
    case "${1}" in
        -h|--help) show_help
            exit 0;;

        -a|--azure_enable)
            addEnvToFile "JWT_PRODUCTION" '"true"'
          ;;

        -i|--tenant_id)
          if [[ ${2} != '-'* ]] || [[ ${2} != '' ]]; then
              AZURE_TENANT_ID=$(echo ${2} | sed -e 's|-|_|g')
              validate_id "${AZURE_TENANT_ID}"
              shift
          fi;;

        -n|--tenant_name)
          if [[ ${2} != '-'* ]] || [[ ${2} != '' ]]; then
              AZURE_TENANT_NAME=${2}; 
              shift
          fi;;

        -c|--client_id)
          if [[ ${2} != '-'* ]] || [[ ${2} != '' ]]; then
              AZURE_CLIENT_ID=${2};
              validate_id "${AZURE_CLIENT_ID}"
              shift
          fi;;

        -s|--client_secret)
          if [[ ${2} != '-'* ]] || [[ ${2} != '' ]]; then
              AZURE_CLIENT_SECRET=${2}; 
              shift
          fi;;

        -r|--redirect_url)
          if [[ ${2} != '-'* ]] || [[ ${2} != '' ]]; then
              REDIRECT_URI=$(echo ${2} | sed -e 's|http://||g; s|https://||g'); 
              shift
          fi;;

        -d|--debug) 
            set -x;;

        *) 
            echo -e "${ERROR} Unknow option: ${1}. See help!"
            exit 1;;
    esac
    shift
  done

  if [ -z ${AZURE_TENANT_ID}  ] ||  [ -z $AZURE_TENANT_NAME  ] || [ -z $AZURE_CLIENT_ID  ]  || [ -z $AZURE_CLIENT_SECRET  ] || [ -z $REDIRECT_URI  ]; then
    echo "Missing one or multiple input parameters! See help"
    exit 1
  fi

  addEnvToFile "AZURE_TENANT_NAME" \'"${AZURE_TENANT_NAME}"\'
  addEnvToFile "AZURE_TENANT_ID" \'"${AZURE_TENANT_ID}"\'
  addEnvToFile "AZURE_CLIENT_ID" \'"${AZURE_CLIENT_ID}"\'
  addEnvToFile "AZURE_CLIENT_SECRET" \'"${AZURE_CLIENT_SECRET}"\'
  addEnvToFile "REDIRECT_URI" \'"${REDIRECT_URI}"\'
  exit 0
}

FM_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
stackEnvFile="${FM_DIR}/.env"
createEnvFile

if [ $# -eq 0 ]; then
 show_help
fi

"$@"
