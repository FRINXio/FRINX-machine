FROM docker.elastic.co/kibana/kibana:6.7.1

RUN bin/kibana-plugin remove frinx-machine-ui-style || true


# ------------------------------------------------------------------------------
# Setting the favicon
# ------------------------------------------------------------------------------

COPY favicons/* /usr/share/kibana/src/ui/public/assets/favicons/

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Fix for a Kibana ipv6 related issue
# ------------------------------------------------------------------------------
# https://github.com/elastic/kibana/pull/29891
# This fix is only contained in versions of Kibana higher than 7, so it's added
# here manually
COPY angular7.0-ipv6fix.js /usr/share/kibana/src/ui/public/chrome/api/angular.js

# ------------------------------------------------------------------------------
# SETTING THE FRINX LOGO
# ------------------------------------------------------------------------------

COPY frinx-machine-ui-style.zip /

# version 6.5.4
#RUN sed -i 's/commons.style.css`,/commons.style.css`,`${bundlePath}\/frinx-machine-ui-style.style.css`,/g' /usr/share/kibana/src/ui/ui_render/ui_render_mixin.js


# version 6.7.1
# Change kibana config files, so that our plugin gets included into the path (or something like that)
RUN sed -i 's/commons.style.css`,/commons.style.css`,`${regularBundlePath}\/frinx-machine-ui-style.style.css`,/g' /usr/share/kibana/src/ui/ui_render/ui_render_mixin.js
RUN sed -i 's@var logoKibana=function.*logoKibana.defaultProps=@var logoKibana=function logoKibana(props){return _react.default.createElement("svg",props,_react.default.createElement("g",{fill:"none",fillRule:"evenodd"}))};logoKibana.defaultProps=@g' /usr/share/kibana/built_assets/dlls/vendors.bundle.dll.js

# Install the plugin itself
RUN bin/kibana-plugin install file:///frinx-machine-ui-style.zip

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# ADD CUSTOM KIBANA CONFIG
# ------------------------------------------------------------------------------
COPY kibana.yml /usr/share/kibana/config/
