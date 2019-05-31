FROM docker.elastic.co/kibana/kibana:6.7.1

RUN bin/kibana-plugin remove frinx-machine-ui-style || true
COPY frinx-machine-ui-style.zip /

# version 6.5.4
#RUN sed -i 's/commons.style.css`,/commons.style.css`,`${bundlePath}\/frinx-machine-ui-style.style.css`,/g' /usr/share/kibana/src/ui/ui_render/ui_render_mixin.js
RUN sed -i 's/commons.style.css`,/commons.style.css`,`${regularBundlePath}\/frinx-machine-ui-style.style.css`,/g' /usr/share/kibana/src/ui/ui_render/ui_render_mixin.js
RUN sed -i 's@var logoKibana=function.*logoKibana.defaultProps=@var logoKibana=function logoKibana(props){return _react.default.createElement("svg",props,_react.default.createElement("g",{fill:"none",fillRule:"evenodd"}))};logoKibana.defaultProps=@g' /usr/share/kibana/built_assets/dlls/vendors.bundle.dll.js


RUN bin/kibana-plugin install file:///frinx-machine-ui-style.zip
