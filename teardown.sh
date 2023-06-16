#!/bin/bash

show_help() {
cat << EOF
DESCRIPTION:

 ${__SCRIPT_NAME} [OPTIONS] 

    - Is aimed to be used for removing FM from the stack and clean docker volumes.
    - Default stack name is set to fm (based on startup.sh script)

OPTIONS:
    -s|--stack-name     set FM stack name (default fm)
    -f|--frinx          delete FM Uniconfig/Workflow-Manager volumes
    -m|--monitoring     delete FM monitoring volumes
    -v|--volumes        delete all FM persistent volumes (FM, Monitoring)
    -c|--cache          delete content of ./config/uniconfig/frinx/uniconfig/cache folder
    -a|--all            delete all volumes and files (except secrets)
    -S|--secrets        delete all docker secrets with prefix frinx_

    -k|--kafka          delete kafka & connector only, remove connector slot from postgresql

    -h|--help           print help
    -w|--wait           maximal waiting time for removing volumes (default 30s)
    -d|--debug          enable verbose
EOF
}

remove_kafka_slot()
{
  echo "###### Cleaning kafka services and conductor slot from postgresql  ######"

  kafka_services=$(docker service ls --filter label=kafka=frinx -q)
  if [[ ${kafka_services} != '' ]]; then
      docker service rm $(docker service ls --filter label=kafka=frinx -q)  || exit 1
      sleep 10
  fi
  echo "Cleaning slots"
  docker exec -it $(docker container ls --filter name=${__STACK_NAME}_postgresql --filter status=running -q) \
      psql -c "SELECT pg_drop_replication_slot('conductor_slot');"
  echo "Execute checkpoint on postgres database"
  docker exec -it $(docker container ls --filter name=${__STACK_NAME}_postgresql --filter status=running -q) \
      psql -c "CHECKPOINT;"
}

delete_stack()
{
  remove_kafka_slot
  echo "###### Cleaning stack ######" 

  docker stack rm ${__STACK_NAME}
  echo ""
}

delete_stuck_containers()
{
  echo "###### Cleaning stuck containers and network ######"
  sleep 20
  local __containers=$(comm -2 -3 <(docker ps -aq --filter name=${__STACK_NAME}_ | sort) <(docker ps -aq --filter name=${__STACK_NAME}_ --filter='status=removing' | sort)) 
  if [[ $__containers != '' ]]; then
    docker rm -f $__containers || true
    docker network rm $(docker network ls --filter name=frinx-machine -q) 2>/dev/null || true
  fi
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
    local __volumes=$(docker volume ls -q -f name=frinx_* )
    local __unused_volumes=$(docker volume ls -q -f name=frinx_* -f dangling=true)

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

__ENV_PATH="${__SCRIPT_PATH}/.env"
__CACHE_PATH="${__SCRIPT_PATH}/config/uniconfig/cache"

__STACK_NAME="fm"
__WAIT_TIME=30
unset __CLEAN_VOLUMES

#ARGUMENTS PARSING
while [ $# -gt 0 ]
do
    case "${1}" in
        -h|--help) show_help
            exit 0;;
        
        -k|--kafka)
            __CLEAN_KAFKA="true";;

        -s|--stack-name)
            if [[ ${2} == "-"* ]] || [[ -z ${2} ]]; then
                echo "Problem with -s|--stack-name parameter. Missing input parameter."
                exit 1
            else
                __STACK_NAME="${2}"; 
                shift
            fi;;

        -f|--frinx)
            __CLEAN_VOLUMES="true";;

        -v|--volumes)
            __CLEAN_VOLUMES="true"
            __CLEAN_MONITORING="true";;
        
        -m|--monitoring)
            __CLEAN_MONITORING="true";;

        -c|--cache)
            __CLEAN_CACHE="true";;

        -a|--all)
            __CLEAN_VOLUMES="true"
            __CLEAN_MONITORING="true"
            __CLEAN_CACHE="true"
            __CLEAN_ENV="true";;

        -S|--secrets)
            __CLEAN_SECRETS="true";;

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
            echo "Unknown option: ${1}"
            show_help
            exit 1;;
    esac
    shift
done

#EXECUTION

if [ -n "${__CLEAN_KAFKA}" ]; then
    remove_kafka_slot
    exit 0
fi

delete_stack
delete_stuck_containers

#CLEAN VOLUMES
if [ -n "${__CLEAN_VOLUMES}" ]; then
    __CURRENT_LOOP=0
    echo "###### Cleaning unused FM volumes ######"
    until [ ${__CURRENT_LOOP} -eq ${__WAIT_TIME} ] || unused_fm_volumes; do
        ((__CURRENT_LOOP=${__CURRENT_LOOP}+1)) 
        sleep 1
    done
    if [[ ${__CURRENT_LOOP} -eq ${__WAIT_TIME} ]] &&  \
        [[ "$(docker volume ls -q -f name=workflow-manager* -f name=uniconfig*)" != "" ]]; then
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
        [[ "$(docker volume ls -q -f name=workflow-manager* -f name=uniconfig*)" != "" ]]; then
        echo "Removing was not successful"
        exit 1
    fi
fi

if [ -n "${__CLEAN_CACHE}" ]; then
    echo "###### Removing content of cache folder ######"
    find "${__CACHE_PATH}" -mindepth 1 -maxdepth 1 -type d -exec sudo rm -vrf {} \;
fi

if [ -n "${__CLEAN_SECRETS}" ]; then
    echo "###### Removing frinx machine secrets ######"
    docker secret rm $(docker secret ls --filter name=frinx_ -q) 
fi