import gmpy2
from phe.paillier import *
import random
import numpy as np
from ECIES import *
import time
from queue import Queue

# 用于生成种子的有关参数
global Q, PRIME, random_state
Q = gmpy2.next_prime(2 ** 1024)  # 大于2^1024的素数
PRIME = gmpy2.next_prime(2 ** 80)
random_state = gmpy2.random_state()


class Client:
    def __init__(self, client_id, num=None):
        self.client_id = client_id
        private_key, public_key = make_keypair()
        self.private_key = private_key
        self.public_key = public_key
        self.Q = Q
        self.num = num
        self.PRIME = PRIME
        self.random_state = random_state
        self.seed = gmpy2.mpz_random(self.random_state, int(self.Q/self.num))  # Q/num是为了防止溢出
        self.test = 1


class TreeNode:
    def __init__(self, client_id=None, public_key=None):
        self.client_id = client_id
        self.public_key = public_key
        self.left = None
        self.right = None
        self.parent = None


def initialize_clients(num_clients):
    clients = []
    for i in range(num_clients):
        clients.append(Client(client_id=i, num=num_clients))
    return clients

# 返回树的根节点
def build_binary_tree(clients):
    nodes = [TreeNode(client.client_id, client.public_key) for client in clients]

    for i in range(len(nodes)):
        left_index = 2 * (i+1) - 1
        right_index = 2 * (i+1)
        if left_index < len(nodes):
            nodes[i].left = nodes[left_index]
            nodes[left_index].parent = i  # 设置左子节点的父节点
        if right_index < len(nodes):
            nodes[i].right = nodes[right_index]
            nodes[right_index].parent = i  # 设置右子节点的父节点

    return nodes[0] if nodes else None


def send_tree_to_clients(root, clients):
    for client in clients:
        client.tree_root = root

# 后序遍历
def traverse_and_process(node, clients):
    if node.left is None and node.right is None:
        # 叶子节点，使用服务器的Paillier公钥加密并创建Message对象
        encrypted_seed = paillier_pub.raw_encrypt(int(clients[node.client_id].seed))
        msg = Message(encrypted_seed)
        msg.encrypt(clients[node.parent].public_key)

        return msg
    else:
        # 内部节点，处理子节点
        left_message = traverse_and_process(node.left, clients) if node.left else Message(1)
        right_message = traverse_and_process(node.right, clients) if node.right else Message(1)

        # 解密子节点的值并与当前节点的种子相加
        if node.left:
            left_message.decrypt(clients[node.client_id].private_key)
            left_value_text = left_message.text
            left_value = int(Padding.removePadding(left_value_text.decode(), mode=0))
        else:
            left_value = 1

        if node.right:
            right_message.decrypt(clients[node.client_id].private_key)
            right_value_text = right_message.text
            right_value = int(Padding.removePadding(right_value_text.decode(), mode=0))
        else:
            right_value = 1

        # 将自己的种子密文和左右子节点发送的密文数值相加
        value = left_value * right_value * paillier_pub.raw_encrypt(int(clients[node.client_id].seed))

        if node.parent is None:  # 根节点直接返回
            return value
        else:
            msg = Message(value)
            msg.encrypt(clients[node.parent].public_key)

            return msg

# 链式聚合，客户端将自己的种子的paillier密文发送给下一个客户端，下一个客户端将自己的种子密文和上一个客户端发送的paillier密文相加然后发送给下一个客户端
def chainagg(clients):
    for i in range(len(clients)):
        if i == 0:
            ciphertext = paillier_pub.raw_encrypt(int(clients[i].seed))
            msg = Message(ciphertext)
            msg.encrypt(clients[i+1].public_key)
        elif i == len(clients)-1:
            msg.decrypt(clients[i].private_key)
            text = msg.text
            value = int(Padding.removePadding(text.decode(), mode=0))
            value *= paillier_pub.raw_encrypt(int(clients[i].seed))
            agg = value
        else:
            msg.decrypt(clients[i].private_key)
            text = msg.text
            value = int(Padding.removePadding(text.decode(), mode=0))
            value *= paillier_pub.raw_encrypt(int(clients[i].seed))
            msg = Message(value)
            msg.encrypt(clients[i+1].public_key)

    return agg


def main():
    st = time.time()
    num = 100

    # 初始化客户端
    clients = initialize_clients(num)

    # 初始化二叉树
    root = build_binary_tree(clients)
    send_tree_to_clients(root, clients)

    global paillier_pub
    paillier_pub, paillier_priv = generate_paillier_keypair(n_length=1024)

    final_value_encrypted = traverse_and_process(root, clients)

    sum = 0
    for i in range(len(clients)):
        sum += int(clients[i].seed)

    agg = paillier_priv.raw_decrypt(final_value_encrypted)  # 树聚合
    # agg = chainagg(clients)  # 链式聚合
    # agg = paillier_priv.raw_decrypt(agg)

    et = time.time()
    print(sum == agg)
    print(f'total time:{et-st}')

if __name__ == "__main__":
    main()

