FROM frinx/frinx_odl:4.2.0.frinx

# copy updated distribution into container (if any available)
RUN mkdir /opt/distribution-frinx-override || true
COPY distribution/ /opt/distribution-frinx-override/
RUN if [ -f /opt/distribution-frinx-override/bin/karaf ]; then rm -R /opt/distribution-frinx && mv /opt/distribution-frinx-override /opt/distribution-frinx; fi

# copy licence to container image
COPY frinx.license.cfg /opt/distribution-frinx/etc

# add karaf features which to run at container startup
RUN ["sed", "-i", \
 "s/#odlFeaturesBoot.*/odlFeaturesBoot= \
  odl-restconf-all, \
  odl-netconf-topology, \
  frinx-cli-all-units, \
  frinx-unified-topology-all-units, \
  frinx-uniconfig-node-manager, \
  frinx-uniconfig-native, \
  frinx-lldp-topology /  \
", \
"/opt/distribution-frinx/etc/org.apache.karaf.features.cfg"]


# Configure
COPY conf/org.ops4j.pax.logging.cfg /opt/distribution-frinx/etc/
COPY odl-wrapper.sh /opt/distribution-frinx/bin/


ENTRYPOINT ["/bin/bash"]
CMD ["/opt/distribution-frinx/bin/odl-wrapper.sh"]
