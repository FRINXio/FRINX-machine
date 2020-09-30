FROM frinx/uniconfig:4.2.4.frinx

# copy updated distribution into container (if any available)
RUN mkdir /opt/uniconfig-frinx-override || true
COPY distribution/ /opt/uniconfig-frinx-override/
RUN if [ -f /opt/uniconfig-frinx-override/run_uniconfig.sh ]; then rm -R /opt/uniconfig-frinx && mv /opt/uniconfig-frinx-override /opt/uniconfig-frinx; fi

# Configure
COPY odl-wrapper.sh /opt/uniconfig-frinx/

# Replace schema folder
COPY schema /opt/uniconfig-frinx/cache/schema


ENTRYPOINT ["/bin/bash"]
CMD ["/opt/uniconfig-frinx/odl-wrapper.sh"]
