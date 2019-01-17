# After persistent change the image shuld be uploaded to Dcoker hub.

# To build and publish:
# cd .../FRINX-machine/conductor/ui
# docker build -f ../../base_images/conductor-ui/Dockerfile -t frinx/conductor-ui_base:latest .
# docker login
# docker push frinx/conductor-ui_base:latest
# docker logout


FROM node:alpine

# Install the required packages for the node build
# to run on alpine
RUN apk update && apk add \
  autoconf \
  automake \
  libtool \
  build-base \
  libstdc++ \
  gcc \
  abuild \
  binutils \
  nasm \
  libpng \
  libpng-dev \
  libjpeg-turbo \
  libjpeg-turbo-dev \
  python

# Make app folders
RUN mkdir -p /app/ui

# Install node modules
COPY package.json /app/ui
COPY package-lock.json /app/ui

RUN cd app/ui \
    && npm install

ENTRYPOINT ["/bin/sh"]
