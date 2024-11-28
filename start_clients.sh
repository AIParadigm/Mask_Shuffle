#!/bin/bash

# 设置编码
export LANG="zh_CN.UTF-8"

# 配置信息
trusted_party_ip="127.0.0.1"
client_count=100
alg=1  # 0为不分组，1为分组
vectorsize=100002

# 设置虚拟环境路径
VENV_PATH="/root/mask_shuffle/.venv"

# 激活虚拟环境
source $VENV_PATH/bin/activate

# 提示运行 trusted_party 和 aggregator
echo "请确保在运行此脚本前已启动 trusted_party 和 aggregator："
echo "  python trusted_party.py $client_count"
echo "  python aggregator.py 1234 $trusted_party_ip"

# 启动客户端进程
for i in $(seq 1 $client_count); do
    echo "启动客户端 $i..."
    python client.py $alg $vectorsize $client_count $trusted_party_ip $i &
done

echo "所有客户端已启动"
