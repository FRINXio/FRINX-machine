#! bin/bash

/usr/share/logstash/bin/logstash -f /etc/logstash/logstash.conf --path.settings /etc/logstash &
sleep 10
/opt/distribution-frinx/bin/karaf



