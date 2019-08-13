#!/usr/bin/env bash

#/home/topology/password-setup.sh
java -Djava.security.egd=file:/dev/./urandom -Xmx2G -jar /home/topology/netconf-testtool/netconf-testtool-1.4.2-Oxygen-SR2.4_2_3_rc2-frinxodl-executable.jar \
--exi false --ssh true --md-sal true --starting-port 1783 --device-count 1 --schemas-dir /home/topology/netconf-testtool/schemas --debug false &
/home/topology/cli-testtool/topologies/sample-topology.sh

