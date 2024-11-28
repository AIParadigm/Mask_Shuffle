import gmpy2
from phe.paillier import *
import time
from privacy_utils import gen_grad, gen_hx, gen_mask, add_mask
from ECIES import *
import pickle

def main():
    paillier_pk, paillier_sk = generate_paillier_keypair(n_length=1024)  # Paillier密钥加密种子
    private_key3, public_key3 = make_keypair()
    private_key2, public_key2 = make_keypair()
    Q = gmpy2.next_prime(2 ** 64)  # 大于2^64的素数
    PRIME = gmpy2.next_prime(2 ** 80)
    random_state = gmpy2.random_state()

    vectorsize = 10000000
    seed1 = gmpy2.mpz_random(random_state, int(Q))
    seed2 = gmpy2.mpz_random(random_state, int(Q))


    encrypted_number1 = paillier_pk.raw_encrypt(int(seed1))
    ciphertext1 = Message(encrypted_number1)
    ciphertext1.encrypt(public_key3)
    ciphertext1.encrypt(public_key2)

    st = time.time()
    encrypted_number2 = paillier_pk.raw_encrypt(int(seed2))
    ciphertext2 = Message(encrypted_number2)
    ciphertext2.encrypt(public_key3)
    ciphertext1.decrypt(private_key2)
    t = time.time() - st
    seed_vector = [ciphertext1, ciphertext2]
    m_seed = pickle.dumps(seed_vector)
    print(f"seed size: {len(m_seed)/1024} KB")

    g = gen_grad(vectorsize)
    hx = gen_hx(vectorsize)

    st = time.time()
    r = gen_mask(hx, seed2, vectorsize, PRIME)
    y = add_mask(g, r, PRIME)
    t += (time.time() - st)
    print(f"P2 time: {t}")

    m_y = pickle.dumps(y)
    print(f"masked grad size: {len(m_y) / (1024 * 1024)} MB")
    print(f"total size: {(len(m_seed) + len(m_y)) / 1024} KB")


if __name__ == "__main__":
    main()