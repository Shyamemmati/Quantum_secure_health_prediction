import json
import os
import time
import hashlib
from typing import Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")  # app data folder
LEDGER_PATH = os.path.join(DATA_DIR, "ledger.jsonl")  # ledger file

def _sha3(data: bytes) -> str:  # compute sha3 hash
    return hashlib.sha3_256(data).hexdigest()

def _read_last_hash() -> Optional[str]:  # return last ledger hash
    if not os.path.exists(LEDGER_PATH):
        return None
    last = None
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                last = obj.get("current_hash")
    return last

def record_event(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:  # append event to ledger
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    prev_hash = _read_last_hash()
    entry = {"ts": int(time.time()), "type": event_type, "payload": payload, "prev_hash": prev_hash}
    body = json.dumps(entry, sort_keys=True).encode("utf-8")
    entry["current_hash"] = _sha3(body)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return {"ok": True, "current_hash": entry["current_hash"], "prev_hash": prev_hash}

def verify_ledger() -> Dict[str, Any]:  # verify chain integrity
    if not os.path.exists(LEDGER_PATH):
        return {"ok": True, "entries": 0}
    prev = None
    count = 0
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            expected_prev = obj.get("prev_hash")
            if expected_prev != prev:
                return {"ok": False, "error": "Broken link", "at_entry": count}
            tmp = obj.copy()
            curr = tmp.pop("current_hash", None)
            body = json.dumps(tmp, sort_keys=True).encode("utf-8")
            recomputed = hashlib.sha3_256(body).hexdigest()
            if curr != recomputed:
                return {"ok": False, "error": "Hash mismatch", "at_entry": count}
            prev = curr
            count += 1
    return {"ok": True, "entries": count}
