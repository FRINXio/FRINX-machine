#!/bin/bash

# Exit on error
set -e

tmp_file='FRINX-machine_test_env.postman_environment_tmp.json'
# To always remove tmp file
trap 'echo remove "$tmp_file"; rm -f $tmp_file' INT TERM EXIT

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

# Ger container ips
odl_ip=$(docker inspect -f "{{with index .NetworkSettings.Networks \"frinx-machine_default\"}}{{.IPAddress}}{{end}}"  odl)
conductor_ip=$(docker inspect -f "{{with index .NetworkSettings.Networks \"frinx-machine_default\"}}{{.IPAddress}}{{end}}"  conductor-server)
sample_topology_ip=$(docker inspect -f "{{with index .NetworkSettings.Networks \"frinx-machine_default\"}}{{.IPAddress}}{{end}}"  sample-topology)

# Copy environment file, so original is not changed
cp ${DIR}/FRINX-machine_test_env.postman_environment.json FRINX-machine_test_env.postman_environment_tmp.json

# Modiy tmp env file, with actual container ips
sed -i -- "s/var_conductor_ip/${conductor_ip}/g" FRINX-machine_test_env.postman_environment_tmp.json
sed -i -- "s/var_odl_ip/${odl_ip}/g" FRINX-machine_test_env.postman_environment_tmp.json
sed -i -- "s/var_sample_topology_ip/${sample_topology_ip}/g" FRINX-machine_test_env.postman_environment_tmp.json

newman run ./FRINX-machine_test.postman_collection.json -e ./FRINX-machine_test_env.postman_environment_tmp.json
