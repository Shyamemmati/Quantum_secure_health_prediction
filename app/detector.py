import numpy as np
import hashlib
import json

def detect_attack(shares):  # simple tamper detection for shares
    try:
        if not shares or not isinstance(shares, list):
            return True  # invalid shares indicate attack
        unique_hashes = {hashlib.sha256(str(s).encode()).hexdigest() for s in shares}  # hash each share
        if len(unique_hashes) != len(shares):
            return True  # duplicate share detected
        for s in shares:
            if not isinstance(s, (list, tuple)) or len(s) != 2:
                return True  # unexpected share structure
        ys = [int(s[1]) for s in shares]
        if len(ys) > 1:
            mean = np.mean(ys)
            std = np.std(ys)
            if std == 0 or (mean != 0 and std / mean < 0.0001):
                return True  # suspiciously identical values
        return False  # no attack detected
    except Exception:
        return True  # on error report attack

def analyze_qber(qber):  # analyze qber value
    try:
        if qber < 0.11:
            return {"ok": True, "message": f"QBER {qber:.4f} secure"}
        elif qber < 0.20:
            return {"ok": True, "message": f"QBER {qber:.4f} mild noise"}
        else:
            return {"ok": False, "message": f"QBER {qber:.4f} high error possible eavesdrop"}
    except Exception:
        return {"ok": False, "message": "Failed to analyze QBER"}
