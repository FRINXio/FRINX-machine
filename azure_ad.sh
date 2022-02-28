#!/usr/bin/env bash

# set env variables from docker secret to service

show_help()
{
local ___script_name="$(basename "${0}")"
cat << EOF
DESCRIPTION:
 Configure Azure AD environment variables in: '${authSecretsTmpFile}' 
  
  - Enable Azure AD authorization in Frinx Machine

  - Transform Tenant ID, replace '-' with '_'

  - Check if all configuration parameters are obtained in .env file
                          
Azure AD environment configuration

  ./${___script_name} configure [OPTIONS] -n -i -c -s -r
      
      -n|--tenant_name     Azure AD Tenant Domain (Primary domain)
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

      -k|--keep_config     Save configuration file to ${authSecretsTmpFile}

    COMMON SETTINGS

      -h|--help    Print this help and exit
      -d|--debug   Enable verbose

Azure AD environment validation

  ./${___script_name} validation

Update auth secrets from tmp file - ${authSecretsTmpFile}

  ./${___script_name} updateSecrets

EOF
}

function updateSecrets {

  local secret_exist=$(docker secret ls -f name=${authSecret} --format {{.Name}})
  for i in ${secret_exist}
  do
    if [[ ${i} == ${authSecret} ]]; then
      docker secret rm "${i}" > /dev/null && echo -e "${INFO} Docker Secrets: Remove old secret ${i}" || exit 1
    fi
  done
  docker secret create "${authSecret}" "${authSecretsTmpFile}" > /dev/null && echo -e "${INFO} Docker Secrets: Created new secret ${authSecret}" || \
  echo -e "${ERROR} Docker secret not imported" | exit 1
}

function createTmpFile {
    cp ${authSecretsFile} ${authSecretsTmpFile}
}


function addEnvToFile {
  unset __old_env_var
  unset __new_env_var
  if [[ -f ${authSecretsTmpFile} ]]; then
    if grep -Fq ${1} ${authSecretsTmpFile}
    then
      __old_env_var=$(grep -n ^${1}= ${authSecretsTmpFile} | cut -d':' -f1)
      __new_env_var="${1}=${2}"
      sed -i "${__old_env_var}d"  "${authSecretsTmpFile}"
      __old_env_var=$((__old_env_var-1))
      sed -i "${__old_env_var}a ${__new_env_var}"  "${authSecretsTmpFile}"
    else
      echo "${1}=${2}" >> ${authSecretsTmpFile} 
    fi 
  fi
}

function setVariableFile {
  local __filePath="${1}"
  echo $__filePath
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
    echo -e "${ERROR} Bad Tenant or Client ID: ${1}"
    exit 1
  fi
}

function validate {

  setVariableFile "${authSecretsTmpFile}"

  if [ -f ${authSecretsTmpFile} ]; then

    if [ -z $AUTH_CLIENT_ID ] ||  [ -z $AUTH_REDIRECT_DOMAIN ] || [ -z $MSAL_AUTHORITY ]  || [ -z $X_TENANT_ID ] || \
      [ -z $OAUTH2_AUTH_URL ] || [ -z $OAUTH2_TOKEN_URL ] || \
      [ -z $AZURE_LOGIN_URL ] || [ -z $AZURE_TENANT_NAME ] || [ -z $AZURE_TENANT_ID ] || \
      [ -z $AZURE_KRAKEND_PLUGIN_CLIENT_ID ] || [ -z $AZURE_KRAKEND_PLUGIN_CLIENT_SECRET ]; then
        echo -e "${ERROR} Missing one or multiple AzureAD config parameters in ${authSecretsTmpFile}!"
        exit 1
    fi

    validate_id "${AZURE_TENANT_ID}"
    validate_id "${X_TENANT_ID}"
    validate_id "${AZURE_KRAKEND_PLUGIN_CLIENT_ID}"

    return
  
  else 
    echo -e "${ERROR} Missing file ${authSecretsTmpFile}!"
    exit 1
  fi

}

function configure {
  while [ $# -gt 0 ]
  do
    case "${1}" in
        -h|--help) show_help
            exit 0;;

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
              AZURE_REDIRECT_URL=$(echo ${2} | sed -e 's|http://||g; s|https://||g'); 
              shift
          fi;;
        
        -k|--keep_config)
          __KEEP_FILE="true";;

        -d|--debug) 
            set -x;;

        *) 
            echo -e "${ERROR} Unknow option: ${1}. See help!"
            exit 1;;
    esac
    shift
  done


  if [ -z ${AZURE_TENANT_ID}  ] ||  [ -z $AZURE_TENANT_NAME  ] || [ -z $AZURE_CLIENT_ID  ]  || [ -z $AZURE_CLIENT_SECRET  ] || [ -z $AZURE_REDIRECT_URL  ]; then
    echo "Missing one or multiple input parameters! See help"
    exit 1
  fi

  createTmpFile

  # KrakenD
  addEnvToFile "AZURE_TENANT_NAME" "${AZURE_TENANT_NAME}"
  addEnvToFile "AZURE_TENANT_ID" "${AZURE_TENANT_ID}"
  addEnvToFile "AZURE_KRAKEND_PLUGIN_CLIENT_ID" "${AZURE_CLIENT_ID}"
  addEnvToFile "AZURE_KRAKEND_PLUGIN_CLIENT_SECRET" "${AZURE_CLIENT_SECRET}"

  # Inventory
  addEnvToFile "X_TENANT_ID" "${AZURE_TENANT_ID}"

  # workflow-proxy
  addEnvToFile "OAUTH2_AUTH_URL" "https://login.microsoftonline.com/${AZURE_TENANT_NAME}/oauth2/v2.0/authorize"

  # frontend
  addEnvToFile "AUTH_CLIENT_ID" "${AZURE_CLIENT_ID}"

  # todo scheme redirect
  addEnvToFile "AUTH_REDIRECT_DOMAIN" "${AZURE_REDIRECT_URL}"
  addEnvToFile "MSAL_AUTHORITY" "https://login.microsoftonline.com/common/"

  updateSecrets

  if [[ ${__KEEP_FILE} != 'true' ]]; then
    rm -f ${authSecretsTmpFile}
  fi

  exit 0
}

ERROR="\033[0;31m[ERROR]:\033[0;0m"
WARNING="\033[0;33m[WARNING]:\033[0;0m"
INFO="\033[0;96m[INFO]:\033[0;0m"
OK="\033[0;92m[OK]:\033[0;0m"

FM_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

authSecret="frinx_auth"
authSecretsFile="${FM_DIR}/config/secrets/${authSecret}"
authSecretsTmpFile="${FM_DIR}/config/secrets/${authSecret}.tmp"

if [ $# -eq 0 ] || [ $1 == '-h' ] || [ $1 == '--help' ] ; then
 show_help
 exit 0
fi

"$@"
