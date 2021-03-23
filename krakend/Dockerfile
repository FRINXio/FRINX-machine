FROM frinx/krakend:1.2.0

USER root
COPY certs /usr/local/share/ca-certificates
RUN  update-ca-certificates

USER krakend