#!/bin/bash
export LANG="zh_CN.UTF-8"


setup_node_ip="127.0.0.1"
client_count=100
alg=1
vectorsize=100002

VENV_PATH="/root/mask_shuffle/.venv"

source $VENV_PATH/bin/activate

echo "  python trusted_party.py $client_count"
echo "  python aggregator.py 1234 $setup_node_ip"

# 启动客户端进程
for i in $(seq 1 $client_count); do
    echo "start client $i..."
    python client.py $alg $vectorsize $client_count $setup_node_ip $i &
done

echo "all client started"
