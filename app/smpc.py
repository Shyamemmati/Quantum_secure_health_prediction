import random
from typing import List, Dict

PRIME = 257  # prime for byte arithmetic

def _eval_poly(coeffs, x, p):  # evaluate polynomial at x modulo p
    result = 0
    power = 1
    for c in coeffs:
        result = (result + c * power) % p
        power = (power * x) % p
    return result

def _lagrange_at_zero(x_s: List[int], y_s: List[int], p: int) -> int:  # lagrange interpolation at zero
    total = 0
    k = len(x_s)
    for i in range(k):
        xi, yi = x_s[i], y_s[i]
        num, den = 1, 1
        for j in range(k):
            if j == i:
                continue
            xj = x_s[j]
            num = (num * (-xj)) % p
            den = (den * (xi - xj)) % p
        inv_den = pow(den, -1, p)
        total += yi * num * inv_den
        total %= p
    return total

def share_secret(secret_hex: str, num_shares: int = 5, threshold: int = 3) -> List[Dict]:  # create secret shares
    secret_bytes = bytes.fromhex(secret_hex)
    if threshold < 2 or threshold > num_shares:
        raise ValueError("threshold must be between 2 and num_shares")
    coeffs_per_byte = []
    for byte in secret_bytes:
        coeffs = [byte] + [random.randint(0, PRIME - 1) for _ in range(threshold - 1)]
        coeffs_per_byte.append(coeffs)
    shares = []
    for x in range(1, num_shares + 1):
        share_bytes = []
        for coeffs in coeffs_per_byte:
            value = _eval_poly(coeffs, x, PRIME)
            share_bytes.append(value)
        shares.append({"x": x, "share": share_bytes})
    return shares  # list of share dicts

def reconstruct_secret(shares: List[Dict]) -> str:  # reconstruct secret hex from shares
    if not shares:
        raise ValueError("No shares provided")
    x_s = [share["x"] for share in shares]
    share_lists = [share["share"] for share in shares]
    length = len(share_lists[0])
    recovered = bytearray()
    for pos in range(length):
        y_s = [sl[pos] for sl in share_lists]
        val = _lagrange_at_zero(x_s, y_s, PRIME)
        recovered.append(val % 256)
    return recovered.hex()  # return hex string
