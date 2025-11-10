# debug_decrypt.py
import sys, os, json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RECORDS = os.path.join(DATA_DIR, "records.json")

def _load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def debug(pid, key_hex):
    recs = _load_json(RECORDS)
    if pid not in recs:
        print("No record for", pid)
        return
    blob = recs[pid]
    nonce = bytes.fromhex(blob["nonce_hex"])
    ct = bytes.fromhex(blob["ciphertext_hex"])
    key = bytes.fromhex(key_hex)
    try:
        pt = AESGCM(key).decrypt(nonce, ct, None)
        print("[SUCCESS] plaintext:", pt.decode())
    except Exception as e:
        print("[FAIL] decrypt error:", repr(e))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python debug_decrypt.py <PATIENT_ID> <KEY_HEX>")
        sys.exit(1)
    debug(sys.argv[1], sys.argv[2])
