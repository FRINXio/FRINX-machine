FROM frinx/frinx_odl:3.1.6.frinx

# copy updated distribution into container (if any available)
RUN mkdir /opt/distribution-frinx-override || true
COPY distribution/ /opt/distribution-frinx-override/
RUN if [ -f /opt/distribution-frinx-override/bin/karaf ]; then rm -R /opt/distribution-frinx && mv /opt/distribution-frinx-override /opt/distribution-frinx; fi

# copy licence to container image
COPY frinx.license.cfg /opt/distribution-frinx/etc

# add karaf features which to run at container startup
RUN ["sed", "-i", \
  "s/featuresBoot=.*/featuresBoot= \
    config, \
    standard, \
    region, \
    package, \
    kar, \
    ssh, \
    management, \
    frinx-installer-backend, \
    cli-topology, \
    unified-topology-all-units, \
    uniconfig-node-manager, \
    cli-southbound-all-units, \
    odl-restconf, \
    odl-netconf-connector-all, \
    frinx-l3vpn-app,  \
    lldp-topology feature /  \
  ", \
  "/opt/distribution-frinx/etc/org.apache.karaf.features.cfg"]


# Install Logstash
# Download and install the Public Signing Key
RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -

# Dependency
RUN apt-get update && apt-get install apt-transport-https

# Save the repository definition
RUN echo "deb https://artifacts.elastic.co/packages/5.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-5.x.list

# Update and install
RUN apt-get update && apt-get install logstash

# Remove x-pack
RUN bin/logstash-plugin remove --purge x-pack || true

# Configure
COPY conf/org.ops4j.pax.logging.cfg /opt/distribution-frinx/etc/

RUN mkdir /mnt/patterns
COPY conf/odl /mnt/patterns/

COPY conf/logstash.conf /etc/logstash/


RUN mkdir /app
COPY start.sh /app

ENTRYPOINT ["/bin/bash"]
CMD ["/app/start.sh"]



