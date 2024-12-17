import random
import numpy as np
import gmpy2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from privacy_utils import gen_grad
import time

def setup(vector_size):
    g = []
    for i in range(vector_size):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(int(i).to_bytes(24, 'big'))
        hx = digest.finalize()
        hx_int = int.from_bytes(hx, "big")
        g.append(hx_int)
    return g

def commit(vector, g, p):
    c = 1
    for i in range(len(vector.tolist())):
        c = gmpy2.c_mod(c * gmpy2.powmod(gmpy2.mpz(g[i]), gmpy2.mpz(vector[i]), p), p)
    return c

def open(c, x, g, p):
    c_v = commit(x, g, p)
    if c_v == c:
        return 1
    else:
        return 0

def mul(c_list, p):
    c_sum = c_list[0]
    for c in c_list[1:]:
        c_sum = gmpy2.c_mod((c_sum*c), p)

    return c_sum

def divide_grad(seed, grad, sub_num):
    np.random.seed(seed)
    indices = np.random.permutation(len(grad))
    sub_size = len(grad) // sub_num
    sub_arrays = []

    for i in range(sub_num):
        start_idx = i * sub_size
        end_idx = (i + 1) * sub_size if i < sub_num - 1 else len(grad)

        sub_array = grad[indices[start_idx:end_idx]]

        if i == sub_num - 1 and len(sub_array) < sub_size:
            padding_size = sub_size - len(sub_array)
            sub_array = np.pad(sub_array, (0, padding_size), 'constant', constant_values=0)

        sub_arrays.append(sub_array)

    return sub_arrays

def batch_commit(vector, seed, sub_num, g, p):
    divided_grad = divide_grad(seed, vector, sub_num)
    batch_vector = np.sum(divided_grad, axis=1)
    batch_c = commit(batch_vector, g, p)

    return batch_c

def batch_open(c_list, c_sum, p):
    transposed_list = [list(item) for item in zip(*c_list)]
    c_mul = []
    for c in transposed_list:
        c_mul.append(mul(c, p))

    if c_mul == c_sum:
        return 1
    else:
        return 0


def main():
    vector_size = 100000
    x1 = gen_grad(vector_size)
    x2 = gen_grad(vector_size)
    x3 = gen_grad(vector_size)
    sum_x = np.sum([x1,x2,x3], axis=0)
    random_int = [random.randint(0, 1000) for _ in range(128)]

    PRIME = gmpy2.next_prime(2 ** 80)
    g = setup(vector_size)

    c1 = []
    c2 = []
    c3 = []
    c_sum = []

    for seed in random_int:
        c1.append(batch_commit(x1, seed, 2, g, PRIME))
        c2.append(batch_commit(x2, seed, 2, g, PRIME))
        c3.append(batch_commit(x3, seed, 2, g, PRIME))
        c_sum.append(batch_commit(sum_x, seed, 2, g, PRIME))

    c_list = [c1,c2,c3]

    print(batch_open(c_list, c_sum, PRIME))


    st = time.time()
    c1 = commit(x1, g, PRIME)
    commit_time = time.time() - st
    c2 = commit(x2, g, PRIME)
    c3 = commit(x3, g, PRIME)

    x = x1 + x2 + x3
    c_list = [c1] * 100001

    cx = commit(x, g, PRIME)

    st = time.time()
    c = mul(c_list, PRIME)
    mul_time = time.time() - st

    st = time.time()
    open(c, x, g, PRIME)
    open_time = time.time() - st

    print(f"commit time: {commit_time}")
    print(f"mul time: {mul_time}")
    print(f"open time: {open_time}")
    print(1)

if __name__ == "__main__":
    main()