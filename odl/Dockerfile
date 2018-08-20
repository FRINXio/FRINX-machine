FROM frinx/frinx_odl:3.1.5.frinx

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
    odl-restconf/  \
  ", \
  "/opt/distribution-frinx/etc/org.apache.karaf.features.cfg"]

CMD ["./bin/karaf"]



