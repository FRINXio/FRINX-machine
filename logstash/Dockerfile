FROM docker.elastic.co/logstash/logstash:6.7.1

RUN rm -f /usr/share/logstash/pipeline/logstash.conf

COPY conf/odl /usr/share/logstash/config/patterns/
COPY conf/logstash.conf /usr/share/logstash/pipeline/
