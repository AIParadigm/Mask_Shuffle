#!/bin/bash
export LANG="zh_CN.UTF-8"

setup_node_ip="127.0.0.1"
alg=1

client_count=100
vectorsize=100000

for i in $(seq 1 $client_count); do
    echo "start client $i..."
    python client.py $alg $vectorsize $client_count $setup_node_ip $i &
done

echo "all client started"
