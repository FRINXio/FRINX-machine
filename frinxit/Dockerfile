FROM node:10.12.0

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Install Gotty 
ADD https://github.com/yudai/gotty/releases/download/v1.0.1/gotty_linux_amd64.tar.gz /usr/src/app
RUN tar -xvf gotty_linux_amd64.tar.gz

# Install nodejs modules used by frinxit
RUN npm install superagent \
  vorpal \
  vorpal-less \
  vorpal-grep \
  vorpal-tour \
  colors \
  superagent-xml2jsparser \
  vorpal-tour

RUN git clone https://github.com/FRINXio/frinxit.git

# port 8888 is for gotty
EXPOSE 8888 4545


CMD ["/usr/src/app/gotty", "--port", "8888", "--permit-write", "--reconnect", "node", "frinxit/frinxit.js"]
