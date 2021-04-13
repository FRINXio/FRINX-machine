FROM frinx/krakend:1.2.0

USER root
COPY certs /usr/local/share/ca-certificates
RUN  apt-get -y update && \
     apt-get -y install curl && \
     update-ca-certificates

USER krakend