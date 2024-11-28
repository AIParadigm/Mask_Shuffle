import copy
import os
import signal
import threading
import time
import zerorpc
from ECIES import *
from phe.paillier import generate_paillier_keypair
import sys
import pickle

class TrustedParty:
    def __init__(self, num_clients):
        self.clients_info = []
        self.num_clients = num_clients
        self.groups = None
        self.total_sum_holder = None
        self.messages_sent = 0
        self.lock = threading.Lock()

    def generate_client_info(self):
        for i in range(self.num_clients):
            client_id = str(i + 1)
            ip_address = f"192.168.1.{client_id}"
            private_key, public_key = make_keypair()
            paillier_pk, paillier_sk = generate_paillier_keypair(n_length=1024)
            self.clients_info.append((client_id, ip_address, public_key, private_key, paillier_pk, paillier_sk))
            print(f"generated client {client_id}，IP: {ip_address}")

    def group_clients(self):
        group_info = copy.deepcopy(self.clients_info)
        # choose total sum holder
        self.total_sum_holder = random.choice(group_info)
        group_info.remove(self.total_sum_holder)
        num_groups = int((self.num_clients-1)/3)
        random.shuffle(group_info)
        groups = [[] for _ in range(num_groups)]

        for idx, client in enumerate(group_info):
            group_index = idx % num_groups
            client_id, ip_address, public_key, _, paillier_pk, _ = client
            groups[group_index].append((client_id, ip_address, public_key, paillier_pk))

        self.groups = groups

    def get_client_info(self, client_id):
        all_client_info = copy.deepcopy(self.clients_info)
        for info in self.clients_info:
            if info[0] == client_id:
                print(f"收到客户端{client_id}的请求")
                # 查找客户端所在的组并发送信息
                for group_index, group in enumerate(self.groups):
                    for client in group:
                        if client[0] == client_id:  # 检查客户端 ID
                            # 发送所在组的信息给客户端
                            group_info = group

                with self.lock:
                    self.messages_sent += 1

                response = {
                    "self_info": pickle.dumps({
                        "client_id": info[0],
                        "ip_address": info[1],
                        "public_key": info[2],
                        "private_key": info[3],
                        "paillier_pk": info[4],
                        "paillier_sk": info[5]
                    }),
                    "all_clients_info": pickle.dumps([
                        {
                            "client_id": c[0],
                            "ip_address": c[1],
                            "public_key": c[2],
                            "paillier_pk": c[4]
                        } for c in all_client_info
                    ]),
                    "total_sum_holder": pickle.dumps({
                        "client_id": self.total_sum_holder[0],
                        "ip_address": self.total_sum_holder[1],
                        "public_key": self.total_sum_holder[2],
                        "paillier_pk": self.total_sum_holder[4]
                    }),
                    "aggregator port": pickle.dumps(1234)
                }

                # 如果客户端不是 total_sum_holder，添加 group_info
                if client_id != self.total_sum_holder[0]:
                    response["group_info"] = pickle.dumps([
                        {
                            "client_id": c[0],
                            "ip_address": c[1],
                            "public_key": c[2],
                            "paillier_pk": c[3]
                        } for c in group_info
                    ])

                return response

        return None

    def get_client_ip(self):
        # 返回指定客户端的信息（包括公私钥）
        all_client_info = copy.deepcopy(self.clients_info)
        response = {
            "all_clients_info": pickle.dumps([
                {
                    "client_id": c[0],
                } for c in all_client_info
            ])
        }

        return response

    def stop_server(self):
        while self.messages_sent < self.num_clients:
            time.sleep(2)
        print("初始化完成")
        pid = os.getpid()  # 获取当前进程的PID
        os.kill(pid, signal.SIGTERM)  # 主动结束指定ID的程序运行


    def run(self):
        self.generate_client_info()
        self.group_clients()
        print("初始化中...")
        stop_thread = threading.Thread(target=self.stop_server)
        stop_thread.start()
        server = zerorpc.Server(self)
        server.bind("tcp://0.0.0.0:4241")
        server.run()

        # 结束服务
        server.stop()  # 停止服务器


'''
python trusted_party.py 100
'''


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python trusted_party.py <客户端数量>")
        sys.exit(1)

    num_clients = int(sys.argv[1])
    # num_clients = 21
    trusted_party = TrustedParty(num_clients)
    trusted_party.run()