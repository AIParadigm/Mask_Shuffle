import time
from privacy_utils import *
import gmpy2
import logging
import numpy as np
import pickle

def main():
    logging.basicConfig(filename='aggreagtor_compute_time.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    Q = gmpy2.next_prime(2 ** 64)  # 大于2^64的素数
    PRIME = gmpy2.next_prime(2 ** 80)
    random_state = gmpy2.random_state()
    seed = []
    grad = []
    n = 100
    vectorsize = 10000000
    hx = gen_hx(vectorsize)
    y = []
    for i in range(n-1):
        # seed.append(gmpy2.mpz_random(random_state, int(Q)))
        g = gen_grad(vectorsize)
        grad.append(g)
        # r = gen_mask(hx, seed[i], vectorsize, PRIME)
        # y.append(np.array(add_mask(g, r, PRIME)))
        print(f"已生成{i+1}个")

    # seed.append((-(sum(seed))))
    g = gen_grad(vectorsize)
    grad.append(g)
    # r = gen_mask(hx, seed[-1], vectorsize, PRIME)
    # y.append(np.array(add_mask(g, r, PRIME)))

    # powers = precompute_powers(n * 10000, PRIME)
    # st = time.time()
    # sum_gradient = aggregate_gard(y, powers, n * 10000, PRIME)
    # t = time.time() - st

    sum_gradient = np.sum(grad, axis=0)
    m_g = pickle.dumps(sum_gradient)
    print(f"aggregated grad size: {len(m_g) / 1024} KB")

    # print(f"Aggregator time: {t}")
    # logging.info(f"Aggregator time: {t}")


if __name__ == "__main__":
    main()


