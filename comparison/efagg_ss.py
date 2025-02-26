import time
import random
import hashlib

import gmpy2
import sympy
from typing import Dict, Tuple
from nacl.bindings import crypto_scalarmult_base, crypto_scalarmult

# Curve25519
CURVE_ORDER = 2 ** 255 - 19
BASE_POINT = crypto_scalarmult_base(bytes([9] + [0] * 31))


def hash_func(s) -> int:
    return int(hashlib.sha256(str(s).encode()).hexdigest(), 16)


def random_scalar() -> int:
    """ Returns a random exponent for the curve 25519 curve, i.e. a random element from Zq. """
    scalar = bytearray(random.getrandbits(8) for _ in range(32))
    scalar[0] &= 248  # Clear the lowest three bits
    scalar[31] &= 127  # Clear the highest bit
    scalar[31] |= 64  # Set the highest bit's 6th bit
    return int.from_bytes(scalar, "little")


def scalarmult(scalar: int, point: bytes) -> bytes:
    """ Curve25519 scalar multiplication (used for generating commitment values) """
    return crypto_scalarmult(scalar.to_bytes(32, "little"), point)


def ss_share_secret(secret: int, n: int, t: int):
    """ VSS using Curve25519 """
    coefficients = [secret] + [random_scalar() for _ in range(t - 1)]

    def f(x: int) -> int:
        """ Polynomial evaluation """
        return sum(coef * pow(x, j, CURVE_ORDER) for j, coef in enumerate(coefficients)) % CURVE_ORDER

    shares = {x: f(x) for x in range(1, n + 1)}

    return shares


def vss_verify(gs: Dict[int, bytes], comj: Dict[int, bytes]) -> bool:
    """ Verify VSS shares """
    for i in gs:
        x = b'\x00' * 32  # Initialize Curve25519 zero point
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
    n = 1000
    t = int(2 * n / 3) + 1
    print(f"n={n}, t={t}")

    Q = gmpy2.next_prime(2 ** 64)
    random_state = gmpy2.random_state()
    secret = int(gmpy2.mpz_random(random_state, int(Q)))

    # Calculate shares
    st = time.time()
    for _ in range(10):
        shares = ss_share_secret(secret, n, t)
    compute_shares_time = time.time() - st

    # Select t random shares for recovery
    shares_for_recovery = dict(random.sample(shares.items(), t))

    st = time.time()
    for _ in range(10):
        recover_s = recover_secret(shares_for_recovery)
    compute_recover_time = time.time() - st

    print("Test recover_secret:", int(recover_s) == int(secret))
    print(f"Share computation time: {compute_shares_time / 10} s")
    print(f"Secret recovery time: {compute_recover_time / 10} s")


if __name__ == "__main__":
    main()

