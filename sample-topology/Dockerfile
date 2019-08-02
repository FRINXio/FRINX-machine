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


ENTRYPOINT ["/bin/bash"]
# the wrapper contains "password-setup.sh" and "sample-topology.sh"
CMD ["./sample-topology-wrapper.sh"]
