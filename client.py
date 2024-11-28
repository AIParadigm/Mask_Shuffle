import copy
import math
import signal
import time
import pickle
import gmpy2
import zerorpc
import numpy as np
import sys
import threading
import avc
from ECIES import *
from phe.paillier import *
import random
from privacy_utils import *
import logging
import os

class FederatedClient:
    def __init__(self, client_id, trusted_party_ip, num, alg):
        self.client_id = client_id
        self.ip = None
        self.trusted_party_ip = trusted_party_ip
        self.ecies_pk = None
        self.ecies_sk = None
        self.paillier_pk = None
        self.paillier_sk = None
        self.all_clients_info = []
        self.group_info = None
        self.total_sum_holder_info = None

        self.seed_vector = []
        self.group_sum_seed = []
        self.sum_seed = None
        self.total_sum_seed = None
        self.gradients_list = []
        self.server = None
        self.client = None

        self.Q = Q
        self.num = int(num)
        self.PRIME = PRIME
        self.random_state = random_state
        self.seed = gmpy2.mpz_random(self.random_state, int(self.Q))
        self.vectorsize = vectorsize
        self.hx = gen_hx(vectorsize)

        self.grad = None
        self.masked_grad = None

        self.comp_time = 0

        self.group_flag = False
        if int(alg) == 1:
            self.group_flag = True

        self.aggregate = False
        self.total_sum_holder = False
        self.group_leader = False
        self.lock = threading.Lock()

    def gen_grad(self):
        gradients = np.round(np.random.random(self.vectorsize) * 2 - 1, 4)
        self.gradients = gradients
        scale_factor = 1e4
        scaled_gradients = gradients * scale_factor
        self.grad = scaled_gradients.astype(np.int32)

    def restore_grad(self, grad):
        scale_factor = 1e4
        restored_gradients = grad.astype(np.float32) / scale_factor
        self.restored_gradients = restored_gradients

    def request_client_info(self):
        try:
            client = zerorpc.Client(timeout=None, heartbeat=None)
            client.connect(f"tcp://{self.trusted_party_ip}:4241")

            client_info = client.get_client_info(self.client_id)
            self_info = pickle.loads(client_info["self_info"])
            self.ip = self_info["ip_address"]
            self.ecies_pk = self_info["public_key"]
            self.ecies_sk = self_info["private_key"]
            self.paillier_pk = self_info["paillier_pk"]
            self.paillier_sk = self_info["paillier_sk"]
            self.aggregator_port = pickle.loads(client_info["aggregator port"])
            self.all_clients_info = pickle.loads(client_info["all_clients_info"])
            self.total_sum_holder_info = pickle.loads(client_info['total_sum_holder'])
            if self.client_id != self.total_sum_holder_info["client_id"]:
                self.group_info = pickle.loads(client_info['group_info'])
            client.close()
            print("setup completed!")
        except Exception as e:
            print(f"setup failed!: {e}")
            pid = os.getpid()
            os.kill(pid, signal.SIGTERM)

    def start_server(self):
        self.server = zerorpc.Server(self)
        self.server.bind(f"tcp://0.0.0.0:{8241 + int(self.client_id)}")
        self.server.run()

    def start_client(self, target_id):
        self.client = zerorpc.Client(timeout=4000, heartbeat=4000)
        self.client.connect(f"tcp://127.0.0.1:{8241 + int(target_id)}")

    def receive_message(self, message):
        with self.lock:
            logging.info(f"client {self.client_id} received message")
            if self.total_sum_holder:
                if not self.group_flag:
                    self.sum_seed = pickle.loads(message)
                else:
                    self.group_sum_seed.append(pickle.loads(message))
            else:
                self.seed_vector = pickle.loads(message)


    def send_vector(self, target_client_id, message):
        self.start_client(target_client_id)
        logging.info(f"client {self.client_id} send seed vector to client {target_client_id}")
        self.client.receive_message(message)

    def send_grad(self, target_client_id):
        self.start_client(target_client_id)
        logging.info(f"client {self.client_id} send grad to aggregator")
        self.client.receive_grad(self.client_id, pickle.dumps(self.masked_grad))
        print("send gard success")

    def send_split_grad(self, target_client_id):
        num_parts = 10
        split_grads = np.array_split(self.masked_grad, num_parts)
        self.partial_grads = [None] * num_parts
        for idx, part in enumerate(split_grads):
            message = pickle.dumps({"part": part, "index": idx, "total_parts": num_parts})
            self.start_client(target_client_id)
            logging.info(f"client {self.client_id} send grad {idx + 1}/{num_parts} to aggregator")
            self.client.receive_split_grad(self.client_id, message)
        print("send gard success")

    def receive_aggregate(self, aggregated_grad):
        with self.lock:
            aggregated_grad = pickle.loads(aggregated_grad)
            self.grad = aggregated_grad
            self.aggregate = True

    def receive_split_aggregate(self, message):
        with self.lock:
            data = pickle.loads(message)
            part, index, total_parts = data["part"], data["index"], data["total_parts"]

            self.partial_grads[index] = part
            logging.info(f"received aggregated grad {index + 1}/{total_parts}")
            if all(part is not None for part in self.partial_grads):
                full_grad = np.concatenate(self.partial_grads)
                self.gradients_list.append(np.array(full_grad))
                logging.info(f"receive aggregated gard success")

                del self.partial_grads
                self.aggregate = True

    def layer_encrypt(self, client_info, current_index, ciphertext):
        for client_info in reversed(client_info[current_index + 1:]):
            logging.info(f"client {self.client_id} use client {client_info['client_id']}'s public key to encrypt")
            ciphertext.encrypt(client_info["public_key"])

    def group_shuffle(self):
        if self.client_id != self.total_sum_holder_info["client_id"]:
            if self.client_id == self.group_info[-1]["client_id"]:
                print(f"client {self.client_id} is group leader")
                logging.info(f"client {self.client_id} is group leader")
                self.group_leader = True
        else:
            logging.info(f"client {self.client_id} hold the sum of all seeds")
            self.total_sum_holder = True
        if not self.total_sum_holder:
            current_index = next((index for index, info in enumerate(self.group_info) if info["client_id"] == self.client_id), None)
        if not self.total_sum_holder and not self.group_leader:
            paillier_pk = self.total_sum_holder_info["paillier_pk"]

            st = time.time()
            encrypted_number = paillier_pk.raw_encrypt(int(self.seed))
            ciphertext = Message(encrypted_number)
            self.layer_encrypt(self.group_info, current_index, ciphertext)
            ct1 = time.time() - st
            self.comp_time += ct1

            if self.client_id != self.group_info[0]["client_id"]:
                while not self.seed_vector:
                    time.sleep(0.005)
                st = time.time()
                for i in range(len(self.seed_vector)):
                    self.seed_vector[i].decrypt(self.ecies_sk)
                ct2 = time.time() - st
                self.comp_time += ct2
            self.seed_vector.append(ciphertext)
            random.shuffle(self.seed_vector)

            message = pickle.dumps(self.seed_vector)
            st1 = time.time()
            self.send_vector(self.group_info[current_index + 1]["client_id"], message)
            et1 = time.time()
            t1 = et1 - st1
            logging.info(f"client {self.client_id} send seed vector cost {t1 * 1000}ms, the size of ciphertext is {len(message) / 1024} KB")
        elif self.group_leader:
            paillier_pk = self.total_sum_holder_info["paillier_pk"]

            st = time.time()
            encrypted_number = paillier_pk.raw_encrypt(int(self.seed))
            ct3 = time.time() - st
            self.comp_time += ct3
            while not self.seed_vector:
                time.sleep(0.005)
            logging.info(f"received seed vector： {self.seed_vector}")

            st = time.time()
            for i in range(len(self.seed_vector)):
                self.seed_vector[i].decrypt(self.ecies_sk)
                self.seed_vector[i] = int(Padding.removePadding(self.seed_vector[i].text.decode(), mode=0))
            for i in range(len(self.seed_vector)):
                encrypted_number *= self.seed_vector[i]
            message = pickle.dumps(encrypted_number)
            ct4 = time.time() - st
            self.comp_time += ct4

            st1 = time.time()
            self.send_vector(self.total_sum_holder_info["client_id"], message)
            et1 = time.time()
            t1 = et1 - st1
            logging.info(f"client {self.client_id} send seed vector cost {t1 * 1000}ms, the size of ciphertext is {len(message) / 1024} KB")
        elif self.total_sum_holder:
            n = int((len(self.all_clients_info)-1)/3)
            while len(self.group_sum_seed) < n:
                time.sleep(0.005)
            logging.info(f"received sum seed of groups {self.group_sum_seed}")

            st = time.time()
            self.seed = 1
            for i in range(len(self.group_sum_seed)):
                self.seed = self.seed * self.group_sum_seed[i] % self.paillier_pk.nsquare

            self.seed = -(self.paillier_sk.raw_decrypt(self.seed))
            ct5 = time.time() - st
            self.comp_time += ct5
        logging.info(f"group based mask shuffling complete，the seed of Pn is {self.seed}")

    def run(self):
        logging.info("*"*50 + "client start" + "*"*50)
        self.request_client_info()
        print('setup complete')

        listening_thread = threading.Thread(target=self.start_server)
        listening_thread.start()

        gen_grad_thread = threading.Thread(target=self.gen_grad())
        gen_grad_thread.start()

        st = time.time()
        self.group_shuffle()
        group_time = time.time() - st
        logging.info(f"client {self.client_id} run group based mask shuffling cost {group_time} s")

        st = time.time()
        self.r = gen_mask(self.hx, self.seed, self.vectorsize, self.PRIME)
        self.masked_grad = add_mask(self.grad, self.r, self.PRIME)
        self.comp_time += time.time() - st

        mask_time = time.time() - st
        logging.info(f"client {self.client_id} compute masked grad cost {mask_time*1000} ms")
        del self.r

        # self.hash_value = avc.commit(self.grad, self.hx, self.PRIME)

        st = time.time()
        if len(self.masked_grad) <= 1000000:
            self.send_grad(self.aggregator_port)
        else:
            self.send_split_grad(self.aggregator_port)
        t4 = time.time() - st
        logging.info(f"client {self.client_id} send masked grad cost {t4*1000}ms, the size of masked grad is {len(pickle.dumps(self.masked_grad))/(1024*1024)} MB")

        while not self.aggregate:
            time.sleep(0.005)
        print('received aggregated grad')


        if self.total_sum_holder:
            logging.info(f"Pn compute time：{self.comp_time}")
        elif self.group_leader:
            logging.info(f"P3 compute time：{self.comp_time}")
        elif self.client_id == self.group_info[-2]["client_id"]:
            logging.info(f"P2 compute time：{self.comp_time}")
        elif self.client_id == self.group_info[0]["client_id"]:
            logging.info(f"P1 compute time：{self.comp_time}")

        logging.info("*" * 50 + "client close" + "*" * 50)
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)

def main():
    if len(sys.argv) != 6:
        print("usage: python client.py <algorithm> <size of gard> <client num> <setup node ip > <client ID>")
        sys.exit(1)

    global Q, PRIME, random_state
    Q = gmpy2.next_prime(2 ** 64)  # 大于2^64的素数
    PRIME = gmpy2.next_prime(2 ** 80)
    random_state = gmpy2.random_state(int(sys.argv[5]))

    global vectorsize

    alg = sys.argv[1]
    vectorsize = int(sys.argv[2])
    num = sys.argv[3]
    setup_node_ip = sys.argv[4]
    client_id = sys.argv[5]

    folder_name = "_".join(sys.argv[1:4])
    base_dir = 'mask_shuffle_log'
    full_folder_path = os.path.join(base_dir, folder_name)
    os.makedirs(full_folder_path, exist_ok=True)

    logging.basicConfig(
        filename=os.path.join(full_folder_path, f'client_{client_id}.log'),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        # encoding='utf-8'
    )

    client = FederatedClient(client_id, setup_node_ip, num, alg)
    client.run()

if __name__ == "__main__":
    main()
