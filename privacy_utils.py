import sys
import time
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import numpy as np
import gmpy2
from phe.paillier import *
from ECIES import *

def gen_grad(len):
    gradients = np.round(np.random.random(len) * 2 - 1, 4)
    scale_factor = 1e4
    scaled_gradients = gradients * scale_factor
    grad = scaled_gradients.astype(np.int32)

    return grad

def gen_hx(len):
    Hx = []
    for i in range(len):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(int(i).to_bytes(24, 'big'))
        hx = digest.finalize()
        hx_int = int.from_bytes(hx, "big")
        Hx.append(hx_int)
    return Hx

def gen_mask(Hx, seed, len, p):
    r = []
    st = time.time()
    for i in range(len):
        r.append(gmpy2.powmod(gmpy2.mpz(Hx[i]), gmpy2.mpz(seed), p))
    # print(f"powmod: {(time.time()-st)}")
    return r

def add_mask(grad, mask, p):
    y = []
    gx = []
    st = time.time()
    for i in range(len(grad)):
        gx.append(gmpy2.powmod(gmpy2.mpz(2), gmpy2.mpz(grad[i]), p))
    # print(f"powmod2: {(time.time()-st)}")

    st = time.time()
    for i in range(len(mask)):
        y.append(gmpy2.c_mod((gx[i]*mask[i]), p))
    # print(f"mulmod: {(time.time()-st)}")
    return y

def aggregate_gard(grads, powers, scale, p):
    globalSum = np.ones(len(grads[0])).astype(np.int32)
    for grad in grads:
        globalSum = globalSum * grad % p
    st = time.time()
    agg_grad = look_up(globalSum, powers, scale, p)
    lt = time.time() - st
    print(f"look up time:{lt}")

    return agg_grad

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
        x_list = powers[(x%scale)]
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

def main():
    Q = gmpy2.next_prime(2 ** 64)
    PRIME = gmpy2.next_prime(2 ** 80)
    random_state = gmpy2.random_state()
    seed = gmpy2.mpz_random(random_state, Q)
    seed1 = -seed
    # seed1 = gmpy2.mpz_random(random_state, Q)
    print(seed1)
    paillier_pk, paillier_sk = generate_paillier_keypair(n_length=1024)
    private_key, public_key = make_keypair()

    st = time.time()
    encrypted_number = paillier_pk.raw_encrypt(int(seed))
    pe = time.time() - st

    encrypted_number1 = paillier_pk.raw_encrypt(int(seed1))

    num_sum = encrypted_number1
    st = time.time()
    for i in range(100):
        num_sum = num_sum * encrypted_number1 % paillier_pk.nsquare
    pa = time.time() - st
    decrypted_sum = paillier_sk.raw_decrypt(num_sum)
    print(f"decrypted_sum: {decrypted_sum}")
    ciphertext = Message(encrypted_number)
    st = time.time()
    ciphertext.encrypt(public_key)
    ee = time.time() - st

    st = time.time()
    ciphertext.decrypt(private_key)
    text = int(Padding.removePadding(ciphertext.text.decode(), mode=0))
    ed = time.time() - st

    st = time.time()
    decrypted_number = paillier_sk.raw_decrypt(text)
    pd = time.time() - st

    vectorsize = 100000
    x1 = gen_grad(vectorsize)
    x2 = gen_grad(vectorsize)
    hx = gen_hx(vectorsize)
    r1 = gen_mask(hx, seed, vectorsize, PRIME)
    r2 = gen_mask(hx, seed1, vectorsize, PRIME)
    y1 = add_mask(x1, r1, PRIME)
    y2 = add_mask(x2, r2, PRIME)

    y = [y1, y2]
    powers = precompute_powers(1000000, PRIME)
    z = aggregate_gard(y, powers, 1000000, PRIME)

    print(seed)
    print(decrypted_number)

    print(f"PE: {pe}")
    print(f"PA: {pa}")
    print(f"PD: {pd}")
    print(f"EE: {ee}")
    print(f"ED: {ed}")

if __name__ == "__main__":
    main()

