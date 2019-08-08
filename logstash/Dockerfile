FROM docker.elastic.co/logstash/logstash:6.7.1

RUN rm -f /usr/share/logstash/pipeline/logstash.conf

COPY conf/odl /usr/share/logstash/config/patterns/
COPY conf/log_readers/logstash.conf /usr/share/logstash/pipeline
COPY conf/pipeline.yml /usr/share/logstash/config/pipeline.yml


ENTRYPOINT ["/bin/sh"]

CMD ["bin/logstash"]