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
    r = gmpy2.powmod(gmpy2.mpz(hx_int), gmpy2.mpz(seed), p)
    for i in range(len(grad)):
        gx.append(int(gmpy2.c_mod((gmpy2.powmod(gmpy2.mpz(2), gmpy2.mpz(grad[i]), p) * r), p)))

    return gx


def precompute_powers(x, p):
    result = {}
    x1 = x * 10
    maxL = 0
    st= time.time()
    for i in range(-x, x):
        z = gmpy2.powmod(gmpy2.mpz(2), gmpy2.mpz(i), p)
        y = z % x1
        if y in result:
            result[y].append(i)
        else:
            result[y] = [i]
        if maxL < len(result[y]):
            maxL = len(result[y])
    print(f"precompute time: {time.time()-st}")
    return result

def look_up(gx, powers, scale, p):
    scale *= 10
    agg_grad = []
    for x in gx:
        x_list = powers[(x % scale)]
        if len(x_list) == 1:
            agg_grad.append(x_list[0])
        elif len(x_list) > 1:
            for i in x_list:
                if x == gmpy2.powmod(gmpy2.mpz(2), gmpy2.mpz(i), p):
                    agg_grad.append(i)
        else:
            print("look up failed")
            sys.exit(1)
    return agg_grad


def process_part(part, total_size, powers, PRIME, result_list):
    vector_size = total_size // 10
    print(f"vector size: {total_size}, part {part} computing grad...")
    grads = []
    for _ in range(10):
        grads.append(gen_grad(vector_size))
    print(f"vector size: {total_size}, part {part} computing y...")
    y = []
    Q = gmpy2.next_prime(2 ** 64)
    random_state = gmpy2.random_state()
    seeds = []
    for _ in range(9):
        seeds.append(int(gmpy2.mpz_random(random_state, int(Q))))
    seed_sum = - sum(seeds)
    seeds.append(seed_sum)

    for i in range(9):
        y.append(np.array(add_mask(grads[i], seeds[i], PRIME)))
    z = np.array(add_mask(grads[9], seeds[9], PRIME))
    del grads, seeds
    print(f"vector size: {total_size}, part {part} aggregating...")
    st = time.time()
    print(f"vector size: {total_size}, part {part} start time: {st}")
    for i in range(9):
        z = z * y[i] % int(PRIME)
    mul_time = time.time() - st
    st1 = time.time()
    x = look_up(z, powers, 10*10000+1, PRIME)
    et = time.time()
    del z

    print(f"vector size: {total_size}, part {part} end time: {et}")
    print(f"vector size: {total_size}, part {part} aggregate time: {et - st}")

    logging.info(f"vector size: {total_size}, part {part} start time: {st}")
    logging.info(f"vector size: {total_size}, part {part} end time: {et}")
    logging.info(f"vector size: {total_size}, part {part} aggregate time: {et - st}")

    result_list[part] = x

def main(total_size, part):
    logging.basicConfig(filename='aggregator_multi_process.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    PRIME = gmpy2.next_prime(2 ** 80)
    powers = precompute_powers(10 * 10000 + 1, PRIME)

    manager = multiprocessing.Manager()
    result_list = manager.dict()

    processes = []
    for i in range(part):
        p = multiprocessing.Process(target=process_part, args=(i, total_size, powers, PRIME, result_list))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    complete_result = []
    for i in range(part):
        complete_result.extend(result_list[i])


if __name__ == '__main__':
    total_size = 100000
    part = 10
    # total_size = int(sys.argv[1])
    # part = int(sys.argv[2])

    main(total_size, part)
