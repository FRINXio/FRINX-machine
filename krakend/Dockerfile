ARG KRAKEND_TAG=latest
FROM frinx/krakend:${KRAKEND_TAG}

USER root
COPY certs /usr/local/share/ca-certificates
RUN  update-ca-certificates

USER krakend