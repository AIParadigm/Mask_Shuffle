import copy
import gmpy2
from phe.paillier import *
import random
import numpy as np
from ECIES import *
import time
import sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

global Q, PRIME, random_state
Q = gmpy2.next_prime(2 ** 1024)  # 大于2^1024的素数
PRIME = gmpy2.next_prime(2 ** 80)
random_state = gmpy2.random_state()


def generate_clients(num_clients):
    return [f'client_{i+1}' for i in range(num_clients)]

def select_clients(clients, num_selected):
    return random.sample(clients, num_selected)

def generate_paillier_keys(selected_clients, bit):
    keys = {}
    for i in range(len(selected_clients)):
        public_key, private_key = generate_paillier_keypair(n_length=bit)
        keys[selected_clients[i]] = (public_key, private_key)
    return keys


def shuffle_vector(vector):
    random.shuffle(vector)
    return vector

# 根据种子和梯度向量生成对应的掩码向量
def gen_mask(seed, modelVector):
    vectorSize = len(modelVector)
    mask = []
    for i in range(0, vectorSize):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(i.to_bytes(24, 'big'))
        hx = digest.finalize()
        hx_int = int.from_bytes(hx, "big")
        mask.append(hx_int * int(seed))
        masked_vector = [(modelVector[j] + int(mask[j])) for j in range(len(modelVector))]

    return masked_vector


def main():
    # 客户端初始化
    start_time = time.time()
    num_clients = 100
    num_selected = 10
    mask_vector = []

    clients = generate_clients(num_clients)
    print("All Clients:", clients)

    selected_clients = select_clients(clients, num_selected)
    print("Selected Clients:", selected_clients)

    # 密钥初始化
    paillier_pub, paillier_priv = generate_paillier_keypair(n_length=1024)
    private_keys, public_keys = generate_keys(selected_clients)
    masks = []

    confuse_client = selected_clients[:-1]
    for client in confuse_client:
        seed = gmpy2.mpz_random(random_state, int(Q/len(selected_clients)))  # 生成自己的种子
        masks.append(seed)

        # 获取当前 client 之后的客户端列表
        current_index = confuse_client.index(client)
        clients_after = confuse_client[current_index + 1:]

        # 加密自己的种子
        paillier_start_time = time.time()
        encrypted_number = paillier_pub.raw_encrypt(int(seed))
        paillier_end_time = time.time()
        paillier_time = paillier_end_time - paillier_start_time
        print('paillier time: ', paillier_time)
        ciphertext = Message(encrypted_number)
        # 逐层加密
        enc_start_time = time.time()
        for client_after in reversed(clients_after):
            ciphertext.encrypt(public_keys[client_after])
        enc_end_time = time.time()
        enc_time = enc_end_time - enc_start_time
        print('enc time:', enc_time)

        if client != confuse_client[0]:
            # 对向量中每个元素进行解密
            dec_start_time = time.time()
            for i in range(len(mask_vector)):
                mask_vector[i].decrypt(private_keys[client])
            dec_end_time = time.time()
            dec_time = dec_end_time - dec_start_time
            print('dec time:', dec_time)

            if client == confuse_client[-1]:
                for i in range(len(mask_vector)):  # 只有最后一次解密需要解码
                    mask_vector[i] = int(Padding.removePadding(mask_vector[i].text.decode(), mode=0))

        print("Size of ciphertext:", sys.getsizeof(ciphertext), "bytes")

        if client != confuse_client[-1]:
            mask_vector.append(ciphertext)
            print("Size of mask_vector:", sys.getsizeof(mask_vector), "bytes")
        else:
            mask_vector.append(encrypted_number)

        shuffle_vector(mask_vector)
        if client == confuse_client[-1]:
            result = mask_vector[0]
            sum_start_time = time.time()
            for i in range(1, len(mask_vector)):
                result *= mask_vector[i]
            sum_end_time = time.time()
            sum_time = sum_end_time - sum_start_time
            print('sum time: ', sum_time)

    dec_result = paillier_priv.raw_decrypt(result)
    masks.append((-dec_result))
    masks = np.array(masks)
    sum = np.sum(masks)
    print('sum: ', sum)
    print('resut: ', dec_result)
    end_time = time.time()
    run_time = end_time - start_time
    print('run time:', run_time)

if __name__ == "__main__":
    main()



