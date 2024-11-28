import pickle

import gmpy2
from phe.paillier import *
import time
from privacy_utils import gen_grad, gen_hx, gen_mask, add_mask


def main():
    seed = []
    cipertext = []
    paillier_pk, paillier_sk = generate_paillier_keypair(n_length=1024)  # Paillier密钥加密种子
    Q = gmpy2.next_prime(2 ** 64)  # 大于2^64的素数
    PRIME = gmpy2.next_prime(2 ** 80)
    random_state = gmpy2.random_state()
    n = 100
    vectorsize = 10000000
    for i in range(n):
        seed.append(gmpy2.mpz_random(random_state, int(Q)))
        cipertext.append(paillier_pk.raw_encrypt(int(seed[i])))

    st = time.time()
    sum_c = 1
    for c in cipertext:
        # sum_c *= c
        sum_c = sum_c * c % paillier_pk.nsquare
    sum_p = -(paillier_sk.raw_decrypt(sum_c))
    t = time.time() - st
    print(sum_p)
    print(sum(seed))
    print(f"PA: {t}")

    g = gen_grad(vectorsize)
    hx = gen_hx(vectorsize)

    st = time.time()
    r = gen_mask(hx, sum_p, vectorsize, PRIME)
    y = add_mask(g, r, PRIME)
    t += (time.time() - st)

    print(f"Pn time: {t}")

    m_y = pickle.dumps(y)
    print(f"masked grad size: {len(m_y) / (1024 * 1024)} MB")
    print(f"total size: {len(m_y) / 1024} KB")


if __name__ == "__main__":
    main()
