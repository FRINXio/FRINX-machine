FROM frinx/micro_base:latest

WORKDIR /home/app
 
COPY ./microservices/netinfra_utils ./netinfra_utils
COPY ./conductor ./conductor
COPY ./wait_for_it.sh .


### Install appliacation setup
WORKDIR /home/app/conductor/client/python
RUN python setup.py install

WORKDIR /home/app/netinfra_utils/workers
CMD [ "python", "main.py" ]
