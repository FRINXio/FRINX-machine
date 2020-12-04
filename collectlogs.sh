#!/bin/bash

# Common functions
function example {
  echo -e "example: $scriptName"
}


function usage {
  echo -e "usage: $scriptName [OPTIONS]\n"
  echo -e "Collect and archive all logs neccessary for troubleshooting."
  echo -e ""
}


function help {
  usage
    echo -e "OPTIONS:"
    echo -e " -h | --help        Display this message and exit"
    echo -e ""
  example
}


function argumentsCheck {
  if [ $1 -eq 0 ]
  then
    return
  fi

  if [ $1 -eq 1 ]
  then
    case $2 in
      -h|--help)
      help
      exit
      ;;

      *)
      echo -e "Uknown argument, see --help for more info \nExiting... \n"
      exit
      ;;
    esac
  fi

  if [ $1 -gt 1 ]
  then
    echo -e "Too many arguments, see --help for more info \nExiting... \n"
    exit
  fi
}


# Collector functions
function getConfiguration {
    local logfileNodes='nodes_configuration.log'
    local logfileServices='services_configuration.log'
    local logfileNetworks='networks_configuration.log'

    # Node configuration
    local nodeList=$(docker node ls --format "{{.Hostname}}")

    echo -e "Swarm nodes" >> $logFolder/$logfileNodes
    docker node ls >> $logFolder/$logfileNodes 2>&1

    for node in $nodeList
    do
        echo -e "\nNode name: $node" >> $logFolder/$logfileNodes
        docker node inspect $node >> $logFolder/$logfileNodes
    done

    # Services configuration
    local serviceList=$(docker service ls --format "{{.Name}}")

    echo -e "Services" >> $logFolder/$logfileServices
    docker service ls >> $logFolder/$logfileServices 2>&1

    for service in $serviceList
    do
        echo -e "\nService name: $service" >> $logFolder/$logfileServices
        docker service inspect $service >> $logFolder/$logfileServices
    done

    # Network configuration
    local networkList=$(docker network ls --format "{{.Name}}")

    echo -e "Networks" >> $logFolder/$logfileNetworks
    docker network ls >> $logFolder/$logfileNetworks

    for network in $networkList
    do
        echo -e "\nNetwork name: $network" >> $logFolder/$logfileNetworks
        docker network inspect $network >> $logFolder/$logfileNetworks
    done
}


function getOverview {
    local logfile='overview.log'

    echo -e "Hostname:" >> $logFolder/$logfile
    hostname -f >> $logFolder/$logfile

    echo -e "\nUptime:" >> $logFolder/$logfile
    uptime >> $logFolder/$logfile

    echo -e "\nDisk:" >> $logFolder/$logfile
    df -h >> $logFolder/$logfile

    echo -e "\nMounts:" >> $logFolder/$logfile
    mount >> $logFolder/$logfile

    echo -e "\n/etc/fstab:" >> $logFolder/$logfile
    cat /etc/fstab >> $logFolder/$logfile

    echo -e "\nNetworks:" >> $logFolder/$logfile
    docker network ls >> $logFolder/$logfile

    echo -e "\nServices:" >> $logFolder/$logfile
    docker service ls >> $logFolder/$logfile 2>&1

    echo -e "\nNodes:" >> $logFolder/$logfile
    docker node ls >> $logFolder/$logfile 2>&1

    echo -e "\nStacks:" >> $logFolder/$logfile
    docker stack ls >> $logFolder/$logfile 2>&1

    stackList=$(docker stack ls --format "{{.Name}}")
    for stack in $stackList
    do
        echo -e "\nStack $stack:" >> $logFolder/$logfile
        docker stack ps $stack >> $logFolder/$logfile
    done

    echo -e "\nStatistics:" >> $logFolder/$logfile
    docker stats --no-stream >> $logFolder/$logfile
}


function getOSLogs {
    local logfile='os.log'

    echo -e "Unit name: docker.service:" >> $logFolder/$logfile
    journalctl -u docker.service --boot >> $logFolder/$logfile

    echo -e "\nUnit name: docker.socket:" >> $logFolder/$logfile
    journalctl -u docker.socket --boot >> $logFolder/$logfile

    local syslogFiles=$(ls /var/log/syslog* | grep -v gz)
    for file in $syslogFiles
    do
        echo -e "\nFile $file:" >> $logFolder/$logfile
        grep docker $file >> $logFolder/$logfile
    done

    local kernFiles=$(ls /var/log/kern* | grep -v gz)
    for file in $kernFiles
    do
        echo -e "\nFile $file:" >> $logFolder/$logfile
        grep docker $file >> $logFolder/$logfile
    done
}


function getServicelogs {
    # TODO: As using "docker service logs" is unreliable and might hang for large logs
    # "docker logs" command is used instead for each running container

    local logfileServices='swarm_services.log'
    local serviceList=$(docker service ls --format "{{.Name}}")

    for service in $serviceList
    do
      echo -e "\nService $service:" >> $logFolder/$logfileServices
      docker logs $(docker ps --format "{{.Names}}" | grep $service) >> $logFolder/$logfileServices 2>&1
    done
}


function archiveIt {
    tar -cjf frinx-logs-$(hostname)-$timestamp.tar.bz2 $logFolder
}


# =======================================
# Program starts here
# =======================================
WARNING='\033[0;33m[WARNING]:\033[0;0m'
INFO='\033[0;96m[INFO]:\033[0;0m'

timestamp=$(date +%Y%m%d-%H%M)
logFolder="log_collection/$timestamp"
scriptName=$0
argumentsCheck $# $@

mkdir -p $logFolder

echo -e "${INFO} Collecting logs - this might take some time, please wait..."
echo -e "${INFO} Getting cluster overview"
getOverview
echo -e "${INFO} Getting cluster configuration"
getConfiguration
echo -e "${INFO} Getting OS logs"
getOSLogs
echo -e "${INFO} Getting swarm services logs"
getServicelogs

echo -e "${INFO} Archiving logs to file:"
echo -e "${INFO} $(pwd)/frinx-logs-$(hostname)-$timestamp.tar.bz2"
archiveIt
