import signal
import time
import pickle
import zerorpc
import threading
from privacy_utils import *
import logging
import os


class Aggregator:
    def __init__(self, port, all_clients_info):
        self.port = port
        self.all_clients_info = all_clients_info
        self.gradients_list = []
        self.num = len(all_clients_info)
        self.PRIME = gmpy2.next_prime(2 ** 80)
        self.powers = None
        self.sended_num = 0
        self.partial_grads = {}
        self.lock = threading.Lock()

    def start_server(self):
        self.server = zerorpc.Server(self)
        self.server.bind(f"tcp://0.0.0.0:{int(self.port)}")
        self.server.run()

    def start_client(self, target_id):
        self.client = zerorpc.Client(timeout=4000, heartbeat=4000)
        self.client.connect(f"tcp://127.0.0.1:{8241 + int(target_id)}")

    def receive_grad(self, client_id, message):
        with self.lock:
            print(f"receive client {client_id}'s grad")
            message = pickle.loads(message)
            self.gradients_list.append(np.array(message))

            if len(self.gradients_list) == len(self.all_clients_info):
                self.aggregation_start_time = time.time()
                self.aggregate_and_broadcast()

        return "grad received"

    def receive_split_grad(self, client_id, message):
        with self.lock:
            data = pickle.loads(message)
            part, index, total_parts = data["part"], data["index"], data["total_parts"]

            if client_id not in self.partial_grads:
                self.partial_grads[client_id] = [None] * total_parts

            self.partial_grads[client_id][index] = part
            print(f"receive client {client_id}'s gard {index + 1}/{total_parts}")

            if all(part is not None for part in self.partial_grads[client_id]):

                full_grad = np.concatenate(self.partial_grads[client_id])
                self.gradients_list.append(np.array(full_grad))
                print(f"client {client_id}'s complete grad has been received")

                del self.partial_grads[client_id]

                if len(self.gradients_list) == len(self.all_clients_info):
                    self.aggregation_start_time = time.time()
                    self.aggregate_and_broadcast()

        return "grad received"

    def aggregate_and_broadcast(self):
        print("aggregate start")
        st = time.time()
        sum_gradient = aggregate_gard(self.gradients_list, self.powers, self.num*10000, self.PRIME)
        agg_time = time.time() - st

        print(f"aggregation time: {agg_time}s")

        self.broadcast_start_time = time.time()
        for client in self.all_clients_info:
            client_id = client['client_id']
            try:
                if len(sum_gradient) <= 1000000:
                    self.start_client(client_id)
                    self.client.receive_aggregate(pickle.dumps(sum_gradient))
                else:
                    self.send_split_grad(sum_gradient, client_id)
                print(f"aggregated grad has been sent to client {client_id}")
                self.sended_num += 1
            except Exception as e:
                print(f"sent to client {client_id} failed: {e}")

    def send_split_grad(self, grad, target_client_id):
        num_parts = 10
        split_grads = np.array_split(grad, num_parts)
        for idx, part in enumerate(split_grads):
            message = pickle.dumps({"part": part, "index": idx, "total_parts": num_parts})
            self.start_client(target_client_id)
            logging.info(f"send grad {idx + 1}/{num_parts} to client {target_client_id}")
            self.client.receive_split_aggregate(message)
        print("all grad has been sent")


    def stop_server(self):
        while self.sended_num != self.num:
            time.sleep(2)
        print("broadcast completed!")
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)

    def run(self):
        self.powers = precompute_powers(self.num*10000, self.PRIME)
        print("precompute completed")
        stop_thread = threading.Thread(target=self.stop_server)
        stop_thread.start()
        listening_thread = threading.Thread(target=self.start_server)
        listening_thread.start()

'''
python aggregator.py 9475 127.0.0.1
'''

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python aggregator.py <port> <ip address>")
        sys.exit(1)

    port = int(sys.argv[1])
    setup_node_ip = sys.argv[2]
    client = zerorpc.Client(timeout=None, heartbeat=None)
    client.connect(f"tcp://{setup_node_ip}:4241")
    response = client.get_client_ip()
    clients_info = pickle.loads(response["all_clients_info"])

    print(clients_info[0]['client_id'])

    aggregator = Aggregator(port, clients_info)
    aggregator.run()