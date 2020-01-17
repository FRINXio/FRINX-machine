FROM frinx/uniconfig:4.2.3.frinx

ARG STORE_PASS
RUN echo ${STORE_PASS}
# copy updated distribution into container (if any available)
RUN mkdir /opt/uniconfig-frinx-override || true
COPY distribution/ /opt/uniconfig-frinx-override/
RUN if [ -f /opt/uniconfig-frinx-override/run_uniconfig.sh ]; then rm -R /opt/uniconfig-frinx && mv /opt/uniconfig-frinx-override /opt/uniconfig-frinx; fi

# copy licence to container image
COPY frinx.license.cfg /opt/uniconfig-frinx/config

# Configure
COPY odl-wrapper.sh /opt/uniconfig-frinx/

# Replace schema folder
COPY schema /opt/uniconfig-frinx/cache/schema

# Configure TLS
RUN mkdir ./tls
WORKDIR /opt/uniconfig-frinx/tls

RUN keytool -keystore .keystore \
 -alias jetty \
 -genkey -keyalg RSA -storetype PKCS12 -validity 365 -keysize 2048 \
 -dname "O=Frinx, L=Bratislava, C=SK" \
 -storepass ${STORE_PASS}

WORKDIR /opt/uniconfig-frinx/config

COPY lighty-uniconfig-config.json lighty-uniconfig-config.json
RUN sed -i "s/.*keystorePassword.*/    \"keystorePassword\":\"${STORE_PASS}\"/" lighty-uniconfig-config.json
RUN cat lighty-uniconfig-config.json

WORKDIR /opt/uniconfig-frinx

ENTRYPOINT ["/bin/bash"]
CMD ["/opt/uniconfig-frinx/odl-wrapper.sh"]
