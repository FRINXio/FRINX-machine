#!/bin/bash
set -e

# Common functions
function example {
  echo -e "example: $scriptName"
}


function usage {
  echo -e "usage: $scriptName [OPTIONS]\n"
  echo -e "Prepares the environment for UniFlow and UniConfig deployment."
}


function help {
  usage
    echo -e "OPTIONS:"
    echo -e " -h | --help        Display this message and exit"
    echo -e " --no-swarm         Installer will NOT setup docker swarm during the installation"
    echo -e "                    Useful in cases where you don't want to use default swarm"
    echo -e "                    configuration and want to setup the swarm on you own."
    echo -e "                    NOTE: You NEED a working swarm prior to running startup.sh"
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

      --no-swarm)
      skipswarm=1
      echo -e "${WARNING} Skipping swarm setup"
      echo -e "${WARNING} Please setup the swarm manually prior to running startup.sh"
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


# =======================================
# Program starts here
# =======================================
dockerInstallVersion="docker-ce=5:18.09.9~3-0~ubuntu-bionic"
dockerComposeInstallVersion="1.22.0"

dockerComposeFileUniconfig='composefiles/swarm-uniconfig.yml'
dockerComposeFileUniflow='composefiles/swarm-uniflow.yml'
dockerComposeFileMicros='composefiles/swarm-uniflow-micros.yml'
scriptName=$0
skipswarm=0

ERROR='\033[0;31m[ERROR]:\033[0;0m'
WARNING='\033[0;33m[WARNING]:\033[0;0m'
INFO='\033[0;96m[INFO]:\033[0;0m'

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

# Workaround to fix composefile when installing
export API_GATEWAY_PORT=443

argumentsCheck $# $@
checkIfRoot
installPrerequisities
checkDockerGroup
pullImages
cleanup
finishedMessage
