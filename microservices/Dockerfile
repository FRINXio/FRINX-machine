FROM python:3.6.10-buster

# Install unzip
RUN apt-get update \
 && apt-get install unzip

WORKDIR /home/app/

# Download and unpack terraform(unpacks to an executable)
ADD https://releases.hashicorp.com/terraform/0.11.10/terraform_0.11.10_linux_amd64.zip .
RUN unzip terraform_0.11.10_linux_amd64.zip

# Download and unpack terraform-aws-vpc pluigin
ADD https://github.com/terraform-aws-modules/terraform-aws-vpc/archive/v1.46.0.zip .
RUN unzip v1.46.0.zip \
 && mv terraform-aws-vpc-1.46.0 terraform-aws-vpc

# Add terraform executable ot path
ENV PATH="$PATH:/home/app"

WORKDIR /home/app

COPY ./microservices/netinfra_utils ./netinfra_utils
COPY ./conductor ./conductor
COPY ./wait_for_it.sh .


### Install appliacation setup
WORKDIR /home/app/conductor/client/python
RUN pip install setuptools
RUN python setup.py install

WORKDIR /home/app/netinfra_utils/workers
CMD [ "python", "main.py" ]
