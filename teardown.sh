#!/bin/bash

show_help() {
cat << EOF
DESCRIPTION:

 ${__SCRIPT_NAME} [OPTIONS] 

    - Is aimed to be used for removing FM from the stack and clean docker volumes.
    - Default stack name is set to fm (based on startup.sh script)

OPTIONS:
    -h|--help           print help
    -s|--stack-name     set FM stack name (default fm)
    -v|--volumes        delete FM volumes
    -m|--monitoring     delete FM monitoring volumes
    -a|--all            delete FM and monitoring volumes
    -w|--wait           maximal waiting time for removing volumes (default 30s)
    -d|--debug          enable verbose
EOF
}

delete_stack()
{
  echo "###### Cleaning stack ######" 
  docker stack rm ${__STACK_NAME}
  echo ""
}

function unused_monitoring_volumes()
{
    local __volumes=$(docker volume ls -q -f name=frinx-monitoring-*)
    local __unused_volumes=$(docker volume ls -q -f name=frinx-monitoring-* -f dangling=true)

    if [ "${__volumes[@]}" != "" ]; then
        if [ "${__volumes[@]}" == "${__unused_volumes[@]}" ]; then
            docker volume rm ${__volumes[@]}
            exit_val=$?
            if [ ${exit_val} -ne 0 ]; then
                echo "Cleaning FM monitoring volumes failed"
            fi
            return ${exit_val}
        else
            return 1
        fi
    else
        echo -e "No FM-monitoring unused volumes\n"    
        return 0
    fi
}

function unused_fm_volumes()
{
    local __volumes=$(docker volume ls -q -f name=frinx_uniflow* -f name=uniconfig-controller_logs -f name=-postgresql_data )
    local __unused_volumes=$(docker volume ls -q -f name=frinx_uniflow* -f name=uniconfig-controller_logs -f name=-postgresql_data -f dangling=true)

    if [ "${__volumes[@]}" != "" ]; then
        if [ "${__volumes[@]}" == "${__unused_volumes[@]}" ]; then
            docker volume rm ${__volumes[@]}
            exit_val=$?
            if [ ${exit_val} -ne 0 ]; then
                echo "Cleaning FM volumes failed"
            fi
            return ${exit_val}
        else
            return 1
        fi
    else
        echo -e "No FM unused volumes\n"    
        return 0
    fi
}


# =======================================
# Program starts here
# =======================================

# DEFAULT VARIABLES
__SCRIPT_NAME="$(basename "${0}")"
__SCRIPT_PATH="$(dirname "$(readlink -f "$0")")"

__STACK_NAME="fm"
__WAIT_TIME=30
unset __CLEAN_VOLUMES

#ARGUMENTS PARSING
while [ $# -gt 0 ]
do
    case "${1}" in
        -h|--help) show_help
            exit 0;;
        
        -s|--stack-name)
            if [[ ${2} == "-"* ]] || [[ -z ${2} ]]; then
                echo "Problem with -s|--stack-name parameter. Missing input parameter."
                exit 1
            else
                __STACK_NAME="${2}"; 
                shift
            fi;;

        -v|--volumes)
            __CLEAN_VOLUMES="true";;
        
        -m|--monitoring)
            __CLEAN_MONITORING="true";;

        -a|--all)
            __CLEAN_VOLUMES="true"
            __CLEAN_MONITORING="true";;

        -w|--wait)
            if [[ -z ${2} ]]; then
                echo "Problem with -w|--wait parameter. Missing input value."
                exit 1
            else
                __WAIT_TIME="${2}"; shift
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

#EXECUTION
delete_stack

#CLEAN VOLUMES
if [ -n "${__CLEAN_VOLUMES}" ]; then
    __CURRENT_LOOP=0
    echo "###### Cleaning unused FM volumes ######"
    until [ ${__CURRENT_LOOP} -eq ${__WAIT_TIME} ] || unused_fm_volumes; do
        ((__CURRENT_LOOP=${__CURRENT_LOOP}+1)) 
        sleep 1
    done
    if [[ ${__CURRENT_LOOP} -eq ${__WAIT_TIME} ]] &&  \
        [[ "$(docker volume ls -q -f name=uniflow* -f name=uniconfig*)" != "" ]]; then
        echo "Removing was not successful"
        exit 1
    fi
fi

#CLEAN MONITORING VOLUMES
if [ -n "${__CLEAN_MONITORING}" ]; then
    __CURRENT_LOOP=0
    echo "###### Cleaning unused FM monitoring volumes ######"
    until [ ${__CURRENT_LOOP} -eq ${__WAIT_TIME} ] || unused_monitoring_volumes; do
        ((__CURRENT_LOOP=${__CURRENT_LOOP}+1)) 
        sleep 1
    done
    if [[ ${__CURRENT_LOOP} -eq ${__WAIT_TIME} ]] &&  \
        [[ "$(docker volume ls -q -f name=uniflow* -f name=uniconfig*)" != "" ]]; then
        echo "Removing was not successful"
        exit 1
    fi
fi
