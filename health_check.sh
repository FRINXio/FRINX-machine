#!/bin/bash

# Common functions
script="startup.sh"

function usage {  
 echo -e "usage: $script [OPTION]  \n"  
}

function help {
  usage
    echo -e "OPTION:"
    echo -e "  --odl   Check only ODL availability"
    echo -e "\n"
  example
}


# Loop arguments
only_odl=false
while [ "$1" != "" ];
do
case $1 in
    --odl)
    only_odl=true
    shift
    ;;
    -h | --help )
    help
    exit
    ;;
    *)    # unknown option
    echo "$script: illegal option $1"
    exit 1 #error
    ;;
esac
done



echo 'Health check:'

declare -i result=0

### Check ODl
echo Check ODL availability:

result=1
for i in {60..1}; do
  response=$(curl --user admin:admin --silent --write-out "HTTPSTATUS:%{http_code}" -H "Accept: application/json" -X GET "http://127.0.0.1:8181/restconf/modules")
  HTTP_STATUS=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
  if [ $HTTP_STATUS -eq 200 ]; 
  then
    echo ODL is ready
    result=0
    break;
  else
    echo "Not available. Waiting for 30 seconds and retrying $(($i-1)) more times."
    sleep 30
  fi
done

if [ "$only_odl" = true ]; then
  exit $result
fi

### Check Elastisearch 
#curl -X GET 'http://localhost:9200/_cluster/health'
./wait_for_it.sh localhost:9200
result+=$?

### Check Microservices
./wait_for_it.sh localhost:6000
result+=$?

### Check Coductor-server
./wait_for_it.sh localhost:8080
result+=$?

### Check conductor-ui
./wait_for_it.sh localhost:5000
result+=$?

### Check dynomite
#curl -X GET 'http://host:22222/ping'
exit $result
