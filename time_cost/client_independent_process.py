import sys
import time
import numpy as np
import gmpy2
import logging
import multiprocessing


def gen_grad(vector_size):
    gradients = np.round(np.random.random(vector_size)*2-1, 4)
    scale_factor = 1e4
    scaled_gradients = gradients * scale_factor
    grad = scaled_gradients.astype(np.int32)
    return grad


def add_mask(grad, seed, p):
    gx = []
    hx_int = 71268528852831316311076975079190540529007687924137045429198239221085821340320

    for i in range(len(grad)):
        r = gmpy2.powmod(gmpy2.mpz(hx_int), gmpy2.mpz(seed), p)
        gx.append(int(gmpy2.c_mod((gmpy2.powmod(gmpy2.mpz(2), gmpy2.mpz(grad[i]), p) * r), p)))

    return gx


def process_part(part, total_size, PRIME, result_list):
    vector_size = total_size // 10
    print(f"vector size: {total_size}, part {part} computing grad...")
    grad = gen_grad(vector_size)
    print(f"vector size: {total_size}, part {part} computing y...")

    Q = gmpy2.next_prime(2 ** 64)
    random_state = gmpy2.random_state()
    seed = int(gmpy2.mpz_random(random_state, int(Q)))
    seed_n = - seed
    st = time.time()
    y = add_mask(grad, seed, PRIME)
    # y = add_mask(grad, seed_n, PRIME)
    et = time.time()

    print(f"vector size: {total_size}, part {part} start time: {st}")
    print(f"vector size: {total_size}, part {part} end time: {et}")
    print(f"vector size: {total_size}, part {part} compute time: {et - st}")

    logging.info(f"vector size: {total_size}, part {part} start time: {st}")
    logging.info(f"vector size: {total_size}, part {part} end time: {et}")
    logging.info(f"vector size: {total_size}, part {part} compute time: {et - st}")

    result_list[part] = y

def main(total_size, part):
    logging.basicConfig(filename='client_independent_process.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    PRIME = gmpy2.next_prime(2 ** 80)
    manager = multiprocessing.Manager()
    result_list = manager.dict()

    processes = []
    for i in range(part):
        p = multiprocessing.Process(target=process_part, args=(i, total_size, PRIME, result_list))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    complete_result = []
    for i in range(part):
        complete_result.extend(result_list[i])


if __name__ == '__main__':
    total_size = 100000000
    part = 10
    # total_size = int(sys.argv[1])
    # part = int(sys.argv[2])

    main(total_size, part)
