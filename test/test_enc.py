import gmpy2
from phe.paillier import *
from ECIES import *
import time


def main():
    Q = gmpy2.next_prime(2 ** 64)  # 大于2^64的素数
    PRIME = gmpy2.next_prime(2 ** 80)
    random_state = gmpy2.random_state()
    seed = []
    encrypted_number = []
    ciphertext = []

    for i in range(1000):
        seed.append(gmpy2.mpz_random(random_state, Q))

    paillier_pk, paillier_sk = generate_paillier_keypair(n_length=1024)
    private_key, public_key = make_keypair()

    st = time.time()
    for i in range(1000):
        e = paillier_pk.raw_encrypt(int(seed[i]))
    pe = time.time()-st

    for i in range(1000):
        encrypted_number.append(paillier_pk.raw_encrypt(int(seed[i])))
        ciphertext.append(Message(encrypted_number[i]))

    st = time.time()
    for i in range(1000):
        ciphertext[i].encrypt(public_key)
    ee = time.time() - st

    st = time.time()
    for i in range(1000):
        ciphertext[i].decrypt(private_key)
        text = int(Padding.removePadding(ciphertext[i].text.decode(), mode=0))
    ed = time.time() - st

    st = time.time()
    for i in range(1000):
        decrypted_number = paillier_sk.raw_decrypt(encrypted_number[i])
    pd = time.time() - st

    print(f"PE: {pe} ms")
    print(f"PD: {pd} ms")
    print(f"EE: {ee} ms")
    print(f"ED: {ed} ms")

if __name__ == "__main__":
    main()



