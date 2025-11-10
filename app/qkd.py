import os
import secrets
from typing import List, Dict, Tuple

def _rand_bits(n: int) -> List[int]:  # random bits from os entropy
    raw = os.urandom((n + 7) // 8)
    bits = []
    for b in raw:
        for i in range(8):
            bits.append((b >> i) & 1)
            if len(bits) == n:
                return bits
    return bits[:n]

def _to_hex(bits: List[int]) -> str:  # pack bits to hex
    by = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        val = 0
        for j, bit in enumerate(chunk):
            val |= (bit & 1) << j
        by.append(val)
    return by.hex()

def qrng_bits(n: int) -> List[int]:  # quantum random bits simulation
    return _rand_bits(n)

def _bb84_sim_once(n_bits: int, eve: bool, eve_rate: float) -> Tuple[List[int], List[int], List[int], List[int]]:
    alice_bits = _rand_bits(n_bits)
    alice_bases = _rand_bits(n_bits)
    bob_bases = _rand_bits(n_bits)
    effective_bits = alice_bits[:]
    if eve and eve_rate > 0:
        for i in range(n_bits):
            if secrets.randbelow(10000) < int(eve_rate * 10000):
                eve_basis = secrets.randbelow(2)
                if eve_basis != alice_bases[i]:
                    if secrets.randbits(1):
                        effective_bits[i] ^= 1
    bob_results = []
    for i in range(n_bits):
        if bob_bases[i] == alice_bases[i]:
            bob_results.append(effective_bits[i])
        else:
            bob_results.append(secrets.randbits(1))
    return alice_bits, alice_bases, bob_results, bob_bases

def _sift_and_qber(alice_bits, alice_bases, bob_results, bob_bases):
    sifted_a, sifted_b = [], []
    for a_bit, a_base, b_bit, b_base in zip(alice_bits, alice_bases, bob_results, bob_bases):
        if a_base == b_base:
            sifted_a.append(a_bit)
            sifted_b.append(b_bit)
    if not sifted_a:
        return [], 1.0
    mismatches = sum(1 for x, y in zip(sifted_a, sifted_b) if x != y)
    qber = mismatches / len(sifted_a)
    return sifted_a, qber

def generate_qkd_key_bb84(bits_needed: int = 256, allow_eavesdrop: bool = False, eve_rate: float = 0.0) -> Dict:
    sifted = []
    total_qber_samples = []
    while len(sifted) < bits_needed:
        a_bits, a_bases, b_bits, b_bases = _bb84_sim_once(max(4 * bits_needed, 1024), allow_eavesdrop, eve_rate)
        round_sifted, qber = _sift_and_qber(a_bits, a_bases, b_bits, b_bases)
        if round_sifted:
            total_qber_samples.append(qber)
            sifted.extend(round_sifted)
    key_bits = sifted[:bits_needed]
    key_hex = _to_hex(key_bits)
    avg_qber = sum(total_qber_samples) / max(1, len(total_qber_samples))
    return {"key_hex": key_hex, "qber": avg_qber, "sifted_len": len(sifted)}

def generate_qkd_key() -> str:  # simple wrapper for compatibility
    res = generate_qkd_key_bb84(bits_needed=256, allow_eavesdrop=False, eve_rate=0.0)
    return res["key_hex"]
