#!/bin/bash

# Common functions
script="health_check.sh"

function usage {
 echo -e "usage: $script [OPTION] [ARGUMENTS]  \n"
}

function help {
  usage
    echo -e "OPTION:"
    echo -e "  -s   Skip given containers"
    echo -e "\n"
    echo -e "ARGUMENTS:"
    echo -e "odl frinxit micros conductor-server conductor-ui dynomite elasticsearch kibana"
  example
}

function example {
  echo -e health_check.sh -s odl frinxit
}


# all container names
valid_containers=("odl" "micros" "conductor-server" "dynomite" "elasticsearch" "kibana" "sample-topology" "logstash" "uniconfig-ui")
containers_to_check=()

curl_odl=( curl --user admin:admin --silent --write-out "HTTPSTATUS:%{http_code}" -H "Accept: application/json" -X GET "http://127.0.0.1:8181/restconf/modules" )
curl_conductor_server=(curl --silent --write-out 'HTTPSTATUS:%{http_code}' -X GET 'http://127.0.0.1:8080/api/metadata/workflow')
curl_elasticsearch=(curl --silent --write-out 'HTTPSTATUS:%{http_code}' -X GET 'http://127.0.0.1:9200/_cluster/health' )
curl_kibana=( curl --silent --write-out 'HTTPSTATUS:%{http_code}' -X GET 'http://127.0.0.1:5601/api/status' )
curl_uniconfig_ui=(curl --silent --write-out 'HTTPSTATUS:%{http_code}' -X GET 'http://127.0.0.1:3000')

# skip test bool
skip=false

# function to check if array contains argument
#valid element array
function valid {
  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1
}


#checks container
# check_container container_name command_to_run_array
function check_container {
local cmd=$2[@]

for i in {500..1}; do

  response=$(${!cmd})
  echo -ne "Waiting for $1 to respond. For $i seconds\033[0K\r"

  HTTP_STATUS=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
  if [ $HTTP_STATUS -eq 200 ];
  then
    echo
    echo "$1 is ready"
    return 0
  fi
  sleep 1
done

echo
echo "$1 not healthy"
return 1

}


# parse arguments and input
while [ "$1" != "" ];

do
case $1 in
    -s | --skip)
    skip=true
    shift
    ;;
    -h | --help )
    help
    exit
    ;;
    -* | --*)    # unknown option
    echo "$script: illegal option $1"
    exit 1 #error
    ;;
    * )    #container names
    valid "$1" "${valid_containers[@]}"
    if [[ $? -eq 0 ]];
    then
      	input_containers+=( "$1" )
    else
	echo "$script: container '$1' not known"
        exit 1
    fi
    shift
    ;;
esac


done



# set containers_to_check
case "$skip" in
  true )                                     # remove given containers from list
    containers_to_check=(${valid_containers[@]})
    for i in "${input_containers[@]}"; do
           containers_to_check=(${containers_to_check[@]//*$i*})
    done
  ;;
  false )                                    # add given containers to list, adds all if not specified
    if [ ${#input_containers[@]} -eq 0 ];
    then
       containers_to_check=("${valid_containers[@]}")
    else
       containers_to_check=("${input_containers[@]}")
    fi
  ;;
  * )
  exit 1
  ;;
esac


result=0

# check containers in array
for i in "${containers_to_check[@]}"; do
  case $i in
    odl )
    check_container $i curl_odl
    result+=$?
    ;;
    frinxit )
    check_container $i curl_frinxit
    result+=$?
    ;;
    micros )
    echo "No exposed ports"
    ;;
    conductor-server )
    check_container $i curl_conductor_server
    result+=$?
    ;;
    conductor-ui )
    check_container $i curl_conductor_ui
    result+=$?
    ;;
    dynomite )
    echo "No exposed ports"
    ;;
    elasticsearch )
    check_container $i curl_elasticsearch
    result+=$?
    ;;
    kibana )
    check_container $i curl_kibana
    result+=$?
    ;;
    sample-topology )
    echo "No exposed ports"
    ;;
    logstash )
    echo "No exposed ports"
    ;;
    uniconfig-ui )
    check_container $i curl_uniconfig_ui
    ;;
    * )
    echo "Invalid container name: $i"
    exit 1
    ;;
  esac
done


exit $result
