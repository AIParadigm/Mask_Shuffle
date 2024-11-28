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

def main():
    vector_size = 100000
    x1 = gen_grad(vector_size)
    x2 = gen_grad(vector_size)
    x3 = gen_grad(vector_size)

    PRIME = gmpy2.next_prime(2 ** 80)

    g = setup(vector_size)

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