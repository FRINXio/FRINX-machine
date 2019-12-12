FROM python:2.7-stretch

WORKDIR /home/topology
 
COPY ./sample-topology/cli-testtool ./cli-testtool
COPY ./wait_for_it.sh .
COPY ./sample-topology/password-setup.sh .
COPY ./sample-topology/sample-topology-wrapper.sh .


WORKDIR /home/topology/cli-testtool/topologies

RUN pip install MockSSH==1.4.5
RUN cat *.sh | grep python > sample-topology.sh \
  && printf "\nwait\n" >> sample-topology.sh \
  && chmod +x sample-topology.sh


## Install java
RUN apt-get update -y && apt-get install -y default-jre

## Change workdir
RUN mkdir -p /home/topology/netconf-testtool/schemas

## Get testtool jar
ADD  https://license.frinx.io/download/netconf-testtool-1.4.2-Oxygen-SR2.4_2_3_rc2-frinxodl-executable.jar /home/topology/netconf-testtool

## copy schemas
COPY ./sample-topology/netconf-testtol/schemas /home/topology/netconf-testtool/schemas
##


ENTRYPOINT ["/bin/bash"]
# the wrapper contains "password-setup.sh" and "sample-topology.sh"
CMD ["/home/topology/sample-topology-wrapper.sh"]
