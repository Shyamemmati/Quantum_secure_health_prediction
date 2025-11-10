import os
import json
from typing import Dict, List
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BASE_DIR = os.path.dirname(__file__)  # path of this file
DATA_DIR = os.path.join(BASE_DIR, "data")  # data folder inside app
RECORDS_PATH = os.path.join(DATA_DIR, "records.json")  # encrypted records file
SHARES_PATH = os.path.join(DATA_DIR, "shares.json")  # secret shares file
DECRYPTED_PATH = os.path.join(DATA_DIR, "decrypted_patients.json")  # decrypted data for ml
os.makedirs(DATA_DIR, exist_ok=True)  # create data folder if missing

def _load_json(path: str) -> dict:  # helper to load json files
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def _save_json(path: str, data: dict):  # helper to save json files
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def save_patient(patient_id: str, patient_data: dict, key_hex: str, shares: List[Dict], threshold: int):  # save and encrypt patient
    aes = AESGCM(bytes.fromhex(key_hex))  # create aesgcm cipher from key
    nonce = os.urandom(12)  # random nonce
    plaintext = json.dumps(patient_data, separators=(",", ":"), sort_keys=True).encode()  # serialize patient
    ciphertext = aes.encrypt(nonce, plaintext, associated_data=None)  # encrypt data

    records = _load_json(RECORDS_PATH)  # load existing records
    records[patient_id] = {"nonce_hex": nonce.hex(), "ciphertext_hex": ciphertext.hex()}  # store encrypted blob
    _save_json(RECORDS_PATH, records)  # save records

    shares_store = _load_json(SHARES_PATH)  # load shares file
    shares_store[patient_id] = {"threshold": threshold, "shares": shares}  # add shares metadata
    _save_json(SHARES_PATH, shares_store)  # save shares

    decrypted = _load_json(DECRYPTED_PATH)  # load decrypted store for ml
    decrypted[patient_id] = {
        "patient_id": patient_id,
        "name": patient_data.get("name", ""),
        "age": patient_data.get("age", ""),
        "condition": patient_data.get("condition", ""),
        "blood_pressure": patient_data.get("blood_pressure", ""),
        "cholesterol": patient_data.get("cholesterol", "")
    }  # minimal decrypted fields
    _save_json(DECRYPTED_PATH, decrypted)  # save decrypted file

def load_record(patient_id: str) -> dict:  # load encrypted record
    return _load_json(RECORDS_PATH).get(patient_id)

def load_shares(patient_id: str) -> dict:  # load shares metadata
    return _load_json(SHARES_PATH).get(patient_id)

def reconstruct_key(patient_id: str, use_first_k: int) -> dict:  # reconstruct key from shares
    container = _load_json(SHARES_PATH)  # read shares file
    if patient_id not in container:
        return {"ok": False, "error": "No shares found for patient"}  # missing shares
    meta = container[patient_id]
    shares_all = meta.get("shares", [])
    threshold = meta.get("threshold", 2)
    if use_first_k < threshold:
        return {"ok": False, "error": f"use_first_k must be greater or equal to threshold {threshold}"}  # check threshold
    if use_first_k > len(shares_all):
        return {"ok": False, "error": "use_first_k exceeds available shares"}  # check available shares
    subset = shares_all[:use_first_k]  # take first k shares
    from app.smpc import reconstruct_secret  # local import to avoid cycles
    key_hex = reconstruct_secret(subset)  # reconstruct secret hex
    return {"ok": True, "key_hex": key_hex}  # return key

def unlock_patient(patient_id: str, key_hex: str) -> dict:  # decrypt patient with key
    records = _load_json(RECORDS_PATH)
    if patient_id not in records:
        return {"ok": False, "error": "Patient record not found"}  # not found
    blob = records[patient_id]
    try:
        key = bytes.fromhex(key_hex)  # key bytes
        aes = AESGCM(key)  # aes object
        nonce = bytes.fromhex(blob["nonce_hex"])  # nonce bytes
        ciphertext = bytes.fromhex(blob["ciphertext_hex"])  # ciphertext bytes
        plaintext = aes.decrypt(nonce, ciphertext, associated_data=None)  # decrypt
        patient = json.loads(plaintext.decode())  # parse patient json

        decrypted = _load_json(DECRYPTED_PATH)
        decrypted[patient_id] = patient  # store decrypted for ml
        _save_json(DECRYPTED_PATH, decrypted)
        return {"ok": True, "patient": patient}  # return patient
    except Exception as e:
        return {"ok": False, "error": f"Invalid key or decryption failed {str(e)}"}  # decrypt error

def load_decrypted_patients() -> dict:  # return decrypted patients for ml
    return _load_json(DECRYPTED_PATH)

def delete_patient(patient_id: str) -> dict:  # delete patient from all stores
    for path in [RECORDS_PATH, SHARES_PATH, DECRYPTED_PATH]:
        data = _load_json(path)
        if patient_id in data:
            del data[patient_id]
            _save_json(path, data)
    return {"ok": True, "deleted": patient_id}  # deletion done

def reset_all() -> dict:  # clear all files
    for path in [RECORDS_PATH, SHARES_PATH, DECRYPTED_PATH]:
        _save_json(path, {})
    return {"ok": True, "message": "All data cleared"}  # return ok
