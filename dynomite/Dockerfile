FROM ubuntu 
 

# Update the repository sources list and Install package Build Essential 
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
 autoconf \
 build-essential \
 dh-autoreconf \
 git \
 libssl-dev \
 libtool \
 software-properties-common \
 redis-server \
 tcl8.5 

# Clone the Dynomite Git
RUN git clone https://github.com/Netflix/dynomite.git
RUN echo 'Git repo has been cloned in your Docker VM'


# COPY vonfig and startup files
COPY ./dynomite/startup.sh dynomite/startup.sh
COPY ./dynomite/redis.conf /etc/redis/


# Move to working directory
WORKDIR dynomite/

# Make executable
RUN chmod +x startup.sh

# Autoreconf 
RUN autoreconf -fvi \
 && ./configure --enable-debug=log \
 && CFLAGS="-ggdb3 -O0" ./configure --enable-debug=full \
 && make \
 && make install

##################### INSTALLATION ENDS ##################### 

# Expose the peer port 
RUN echo 'Exposing peer port 8101'
EXPOSE 8101 

# Expose the underlying Redis port 
RUN echo 'Exposing Redis port 22122'
EXPOSE 22122 

# Expose the stats/admin port
RUN echo 'Exposing stats/admin port 22222'
EXPOSE 22222 

# Default port to acccess Dynomite
RUN echo 'Exposing client port for Dynomite 8102'
EXPOSE 8102

# Setting overcommit for Redis to be able to do BGSAVE/BGREWRITEAOF
RUN sysctl vm.overcommit_memory=1

# Set the entry-point to be the startup script
ENTRYPOINT ["/dynomite/startup.sh"]
