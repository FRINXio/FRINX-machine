FROM frinx/uniconfig:4.2.3-rc2

# copy updated distribution into container (if any available)
RUN mkdir /opt/distribution-frinx-override || true
COPY distribution/ /opt/distribution-frinx-override/
RUN if [ -f /opt/distribution-frinx-override/run-lighty-uniconfig-distribution.sh ]; then rm -R /opt/distribution-frinx && mv /opt/distribution-frinx-override /opt/distribution-frinx; fi

# copy licence to container image
COPY frinx.license.cfg /opt/distribution-frinx/config

# Configure
COPY odl-wrapper.sh /opt/distribution-frinx/

# Replace schema folder
COPY schema /opt/distribution-frinx/cache/schema


ENTRYPOINT ["/bin/bash"]
CMD ["/opt/distribution-frinx/odl-wrapper.sh"]
