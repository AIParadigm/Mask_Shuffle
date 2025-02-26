import time
import random
import hashlib

import gmpy2
import sympy
from typing import Dict, Tuple
from nacl.bindings import crypto_scalarmult_base, crypto_scalarmult

# Base point of Curve25519
CURVE_ORDER = 2**255 - 19  # Order of the finite field of Curve25519
BASE_POINT = crypto_scalarmult_base(bytes([9] + [0] * 31))  # 9 is the base point defined by Curve25519

def hash_func(s) -> int:
    """ Calculate SHA-256 hash value and convert to integer """
    return int(hashlib.sha256(str(s).encode()).hexdigest(), 16)

def random_scalar() -> int:
    """ Generate a private key (random number) allowed by Curve25519 """
    scalar = bytearray(random.getrandbits(8) for _ in range(32))
    scalar[0] &= 248  # Clear the lowest three bits
    scalar[31] &= 127  # Clear the highest bit
    scalar[31] |= 64   # Set the highest bit's 6th bit
    return int.from_bytes(scalar, "little")

def scalarmult(scalar: int, point: bytes) -> bytes:
    """ Scalar multiplication for Curve25519 (used to generate commitment value) """
    return crypto_scalarmult(scalar.to_bytes(32, "little"), point)

def vss_share_secret(secret: int, n: int, t: int):
    """ VSS using Curve25519 """
    coefficients = [secret] + [random_scalar() for _ in range(t - 1)]

    def f(x: int) -> int:
        """ Polynomial calculation """
        return sum(coef * pow(x, j, CURVE_ORDER) for j, coef in enumerate(coefficients)) % CURVE_ORDER

    shares = {x: f(x) for x in range(1, n + 1)}

    # Calculate G^s_i as commitment
    gs = {i: scalarmult(shares[i], BASE_POINT) for i in range(1, n + 1)}

    # Calculate s_i * H(G^s_i) as verification value
    sgs = {i: shares[i] * hash_func(gs[i]) for i in range(1, n + 1)}

    # Calculate commitment values
    comj = {j: scalarmult(coefficients[j], BASE_POINT) for j in range(t)}

    return shares, gs, comj, sgs

def vss_verify(gs: Dict[int, bytes], comj: Dict[int, bytes]) -> bool:
    """ Verify VSS shares """
    for i in gs:
        x = b'\x00' * 32  # Initialize the zero point of Curve25519
        for j in comj:
            x = crypto_scalarmult(pow(i, j, CURVE_ORDER).to_bytes(32, "little"), comj[j])
        if gs[i] != x:
            return False
    print("vss_verify:", True)
    return True

def lagrange_coefficient(i: int, keys) -> int:
    """ Calculate Lagrange interpolation coefficient """
    result = 1
    for j in keys:
        if i != j:
            result *= j * sympy.mod_inverse((j - i) % CURVE_ORDER, CURVE_ORDER)
            result %= CURVE_ORDER
    return result

def recover_secret(shares: Dict[int, int]) -> int:
    """ Recover secret using Lagrange interpolation """
    return sum(share * lagrange_coefficient(i, shares.keys()) for i, share in shares.items()) % CURVE_ORDER

def main():
    n = 400
    t = int(2 * n / 3) + 1
    print(f"n={n}, t={t}")

    Q = gmpy2.next_prime(2 ** 64)
    random_state = gmpy2.random_state()
    secret = int(gmpy2.mpz_random(random_state, int(Q)))

    # Calculate shares
    st = time.time()
    for _ in range(10):
        shares, gs, comj, sgs = vss_share_secret(secret, n, t)
    compute_shares_time = time.time() - st

    # Select t random shares for recovery
    shares_for_recovery = dict(random.sample(shares.items(), t))

    st = time.time()
    for _ in range(10):
        recover_s = recover_secret(shares_for_recovery)
    compute_recover_time = time.time() - st

    print("Test recover_secret:", int(recover_s) == int(secret))
    print(f"Time to compute shares: {compute_shares_time / 10} s")
    print(f"Time to recover secret: {compute_recover_time / 10} s")

if __name__ == "__main__":
    main()

