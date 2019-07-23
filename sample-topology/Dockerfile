FROM python:2.7-stretch

WORKDIR /home/topology
 
COPY ./sample-topology/cli-testtool ./cli-testtool
COPY ./wait_for_it.sh .

WORKDIR /home/topology/cli-testtool/topologies

RUN pip install MockSSH==1.4.5
RUN cat *.sh | grep python > sample-topology.sh \
  && printf "\nwait\n" >> sample-topology.sh \
  && chmod +x sample-topology.sh

ENTRYPOINT ["/bin/bash"]
CMD ["./sample-topology.sh"]
