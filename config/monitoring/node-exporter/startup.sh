#!/bin/sh

echo $NODE_ID

if [ "${NODE_ID}" == "" ]; then
    echo "ERROR: NODE_ID ENV is required for this container to run"
    exit 1
fi

NODE_NAME=$(cat /etc/nodename)
echo "node_meta{node_id=\"$NODE_ID\", container_label_com_docker_swarm_node_id=\"$NODE_ID\", node_name=\"$NODE_NAME\"} 1" > /home/node-meta.prom

/bin/node_exporter --collector.textfile.directory=/home/ --path.procfs=/host/proc --path.sysfs=/host/sys --path.rootfs=/host --collector.filesystem.ignored-mount-points="^(/rootfs|/host|)/(sys|proc|dev|host|etc)($$|/)" --collector.filesystem.ignored-fs-types="^(sys|proc|auto|cgroup|devpts|ns|au|fuse\.lxc|mqueue)(fs|)$$"
