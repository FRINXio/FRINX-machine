FROM docker.elastic.co/kibana/kibana:6.7.1

# Remove x-pack
#RUN bin/kibana-plugin remove x-pack || true



#RUN bin/kibana-plugin remove frinx-machine-ui-style || true

COPY frinx-machine-ui-style.zip /
#RUN sed -i "s/bundleFile('commons.style.css')/bundleFile('commons.style.css'),bundleFile('frinx-machine-ui-style.style.css')/g" /usr/share/kibana/src/ui/views/ui_app.jade
#RUN bin/kibana-plugin install file:///frinx-machine-ui-style.zip
