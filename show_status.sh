#!/usr/bin/env bash


valid_containers=(
    "uniconfig"
    "conductor-server"
    "postgresql"
    "elasticsearch"
    "kibana"
    "uniconfig-ui"
    "micros"
    "dynomite"
    "sample-topology"
    "logstash"
    "portainer"
)

# calls the function with the correct service name
get_service_status() {
    service=$1
    function="check_$service"
    $function
}

get_container_status() {
    container_name=$1
    docker ps --filter="name=^$container_name\$" --format "{{.Status}}"
}

print_container_status() {
    container_name="$1"
    status="$2"

    echo $status | grep -q "Up"

    if [[ $?  -eq 0 ]]
    then
        echo "$container_name docker status : $status OK"
    else
        echo "$container_name docker status : $status NOT OK"
    fi
}

check_host_port() {
    service=$1
    host=$2
    port=$3

    # https://www.gnu.org/savannah-checkouts/gnu/bash/manual/bash.html#Redirections
    (echo > /dev/tcp/$host/$port) 2>/dev/null

    if [[ $? -eq 0 ]]
    then
        echo "Connection to $service on $host:$port successfull"
    else
        echo "Connection to $service on $host:$port unsuccessfull"
    fi
}

check_service_running() {
    host="$1"
    port="$2"
    pathname="$3"
    expected_http_code="$4"

    ret_http_code=$(curl -X GET -s -o /dev/null -w "%{http_code}" "$host:$port$pathname")
    if [[ $expected_http_code == $ret_http_code ]]
    then
        echo "Service at $host:$port$pathname running successfully,"
        echo "the expected http_code was '$expected_http_code' and received '$ret_http_code'"
    else
        echo "Service at $host:$port$pathname NOT running successfully,"
        echo "the expected http_code was '$expected_http_code' but received '$ret_http_code'"
    fi
}

print_final_service_status() {
    local container_name="$1"
    local docker_status="$2"
    local container_tcp_connection="$3"
    local container_service_connection="$4"

    if [[ "$docker_status" =~ "NOT" ]] || \
       [[ "$container_tcp_connection" =~ "unsuccessfull" ]] || \
       [[ "$container_service_connection" =~ "NOT" ]]
    then
        echo "$container_name has some problems:"
        echo "$docker_status"
        echo "$container_tcp_connection"
        echo "$container_service_connection"
    else
        echo "$container_name ... OK"

    fi

}

check_complete() {
    local container_name="$1"
    local container_port="$2"
    local expected_http_code="$3"
    local pathname="$4"

    local docker_status=$( get_container_status "$container_name" )
    docker_status=$(print_container_status "$container_name" "$docker_status")
    local container_tcp_connection=$(check_host_port "$container_name" "localhost" "$container_port")
    local container_service_connection=$(check_service_running "localhost" "$container_port" "$pathname" "$expected_http_code")

    print_final_service_status "$container_name" "$docker_status" "$container_tcp_connection" "$container_service_connection"
}

check_docker_only() {
    local container_name="$1"

    local docker_status=$( get_container_status "$container_name" )
    docker_status=$(print_container_status "$container_name" "$docker_status")

    if [[ "$docker_status" =~ "NOT" ]]
    then
        echo "$container_name has some problems:"
        echo "$docker_status"
    else
        echo "$container_name ... OK"

    fi
}

check_uniconfig() {
    local container_name="uniconfig"
    local container_port="8181"
    local expected_http_code="401"
    local pathname=""

    check_complete "$container_name" "$container_port" "$expected_http_code" "$pathname"

}

check_conductor_server() {
    local container_name="conductor-server"
    local container_port="8080"
    local expected_http_code="200"
    local pathname="/index.html"

    check_complete "$container_name" "$container_port" "$expected_http_code" "$pathname"
}

check_postgresql() {
    local container_name="postgresql"
    local container_port="5432"

    local docker_status=$( get_container_status "$container_name" )
    docker_status=$(print_container_status "$container_name" "$docker_status")
    local container_tcp_connection=$(check_host_port "$container_name" "localhost" "$container_port")
    local container_service_connection=$(docker exec -it "$container_name" "pg_isready" 2>&1)

    if [[ "$docker_status" =~ "NOT" ]] || \
       [[ "$container_tcp_connection" =~ "unsuccessfull" ]] || \
       [[ ! "$container_service_connection" =~ "accepting" ]]
    then
        echo "$container_name has some problems:"
        echo "$docker_status"
        echo "$container_tcp_connection"
        echo "$container_service_connection"
    else
        echo "$container_name ... OK"

    fi

}

check_elasticsearch() {
    local container_name="elasticsearch"
    local container_port="9200"
    local expected_http_code="200"
    local pathname=""

    check_complete "$container_name" "$container_port" "$expected_http_code" "$pathname"
}

check_kibana() {
    local container_name="kibana"
    local container_port="5601"
    local expected_http_code="200"
    local pathname="/app/kibana"

    check_complete "$container_name" "$container_port" "$expected_http_code" "$pathname"
}

check_uniconfig_ui() {
    local container_name="uniconfig-ui"
    local container_port="9200"
    local expected_http_code="200"
    local pathname=""

    check_complete "$container_name" "$container_port" "$expected_http_code" "$pathname"
}

check_portainer() {
    local container_name="portainer"
    local container_port="9000"
    local expected_http_code="200"
    local pathname=""

    check_complete "$container_name" "$container_port" "$expected_http_code" "$pathname"

    if [[ $(get_container_status "$container_name") == "" ]]
    then
        echo
        printf "%s\n" "By default, 'portainer' exits if no admin account was created in " \
            "the last 5 minutes since it's starup. To start 'portainer' again, " \
            "you can run the 'startup.sh' script again."
    fi
}

check_micros() {
    local container_name="micros"
    check_docker_only "$container_name"
}

check_dynomite() {
    local container_name="dynomite"
    check_docker_only "$container_name"
}

check_sample_topology() {
    local container_name="sample-topology"
    check_docker_only "$container_name"
}

check_logstash() {
    local container_name="logstash"
    check_docker_only "$container_name"
}

main() {
    for c in "${valid_containers[@]}"
    do
        norm_container_name=$(echo $c | sed 's/-/_/g')
        echo "--------------------------------"
        get_service_status $norm_container_name
    done
}

main
