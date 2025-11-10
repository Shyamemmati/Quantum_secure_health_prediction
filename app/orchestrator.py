import json
from app.data_generator import input_patient_data  # interactive input function
from app.storage import save_patient, load_record, delete_patient, reset_all, reconstruct_key, unlock_patient, load_decrypted_patients, load_shares  # storage functions
from app.qkd import generate_qkd_key  # qkd key generator
from app.smpc import share_secret  # secret sharing
from app.detector import detect_attack  # attack detector
from app.ml_model import train_model as model_train, predict as predict_patient_risk  # ml functions

_unlocked_keys_cache = {}  # cache for unlocked keys
_unlocked_patients_cache = {}  # cache for decrypted patient data

def register_patient(pid, name, age, condition, bp, chol, num_shares=5, threshold=3):  # register patient flow
    try:
        existing = load_record(pid)  # check duplicate
        if existing:
            return {"error": "already registered"}  # duplicate error
        if threshold > num_shares:
            return {"error": "threshold cannot be greater than total shares"}  # threshold invalid
        key_hex = generate_qkd_key()  # generate key
        shares = share_secret(key_hex, num_shares, threshold)  # create shares
        attack_detected = detect_attack(shares)  # check shares integrity
        patient = {"patient_id": pid, "name": name, "age": age, "condition": condition, "blood_pressure": bp, "cholesterol": chol, "key_hex": key_hex}
        save_patient(pid, patient, key_hex, shares, threshold)  # save everything
        _unlocked_keys_cache[pid] = key_hex  # cache key for demo use
        _unlocked_patients_cache[pid] = patient  # cache patient
        return {"ok": True, "patient_id": pid, "key_hex_for_demo": key_hex, "threshold": threshold, "attack_detected": attack_detected}
    except Exception as e:
        return {"error": str(e) or "Unknown error"}

def reconstruct_key_wrapper(pid, num_shares):  # wrapper to reconstruct key
    try:
        return reconstruct_key(pid, num_shares)
    except Exception as e:
        return {"ok": False, "error": str(e) or "Error reconstructing key"}

def unlock_patient_with_cache(pid, key_hex):  # unlock patient using cache if possible
    cached_key = _unlocked_keys_cache.get(pid)
    if cached_key == key_hex and pid in _unlocked_patients_cache:
        return {"ok": True, "patient": _unlocked_patients_cache[pid]}  # return cached patient
    res = unlock_patient(pid, key_hex)  # try unlock through storage
    if res.get("ok"):
        _unlocked_keys_cache[pid] = key_hex
        _unlocked_patients_cache[pid] = res["patient"]
    return res

def unlock_patient_wrapper(pid, key_hex):  # public wrapper
    return unlock_patient_with_cache(pid, key_hex)

def train_model():  # train ml model via ml module
    try:
        return model_train()
    except Exception as e:
        return {"error": str(e) or "Model training failed"}

def predict_risk(pid, key_hex=None):  # predict risk for pid
    try:
        if key_hex:
            unlocked = unlock_patient_with_cache(pid, key_hex)
            if not unlocked.get("ok"):
                return {"ok": False, "error": "Invalid key or patient not found"}
            patient = unlocked["patient"]
        else:
            patient = _unlocked_patients_cache.get(pid)
            if not patient:
                return {"ok": False, "error": "Patient not unlocked and no key provided"}
        return predict_patient_risk(patient)
    except Exception as e:
        return {"ok": False, "error": str(e) or "Prediction failed"}

def delete_patient_wrapper(pid):  # delete patient data
    try:
        _unlocked_keys_cache.pop(pid, None)
        _unlocked_patients_cache.pop(pid, None)
        record = load_record(pid)
        if not record:
            return {"error": "not found"}
        delete_patient(pid)
        return {"ok": True, "message": f"Patient {pid} deleted successfully"}
    except Exception as e:
        return {"error": str(e) or "Deletion failed"}

def reset_all_data():  # reset all data and clear caches
    try:
        result = reset_all()
        _unlocked_keys_cache.clear()
        _unlocked_patients_cache.clear()
        return result
    except Exception as e:
        return {"error": str(e) or "Reset failed"}

def preload_demo_dataset():  # create demo patients and train ml model
    try:
        from app.smpc import reconstruct_secret  # local import
        from app.storage import load_record, load_shares, unlock_patient  # storage helpers
        reset_all()
        _unlocked_keys_cache.clear()
        _unlocked_patients_cache.clear()
        demo_patients = [
            ("P300", "Patient300", 25, "Healthy", "115 75", 160),
            ("P301", "Patient301", 35, "Healthy", "120 80", 180),
            ("P302", "Patient302", 28, "Asthma", "125 82", 185),
            ("P303", "Patient303", 40, "Asthma", "128 85", 200),
            ("P304", "Patient304", 50, "Obesity", "135 88", 210),
            ("P305", "Patient305", 32, "Obesity", "140 90", 190),
            ("P306", "Patient306", 45, "Hyperlipidemia", "138 86", 230),
            ("P307", "Patient307", 55, "Hyperlipidemia", "142 92", 240),
            ("P308", "Patient308", 30, "Autoimmune", "118 78", 200),
            ("P309", "Patient309", 48, "Autoimmune", "125 85", 210),
            ("P310", "Patient310", 29, "Corona", "122 80", 195),
            ("P311", "Patient311", 38, "Corona", "130 85", 205),
            ("P312", "Patient312", 46, "Diabetes", "145 95", 220),
            ("P313", "Patient313", 52, "Diabetes", "150 98", 230),
            ("P314", "Patient314", 60, "Hypertension", "155 100", 240),
            ("P315", "Patient315", 65, "Hypertension", "160 105", 250),
            ("P316", "Patient316", 55, "Cancer", "140 90", 250),
            ("P317", "Patient317", 62, "Cancer", "150 95", 260),
            ("P318", "Patient318", 58, "Heart Attack", "160 100", 270),
            ("P319", "Patient319", 70, "Heart Attack", "165 105", 280),
            ("P320", "Patient320", 50, "CKD", "148 92", 245),
            ("P321", "Patient321", 67, "CKD", "155 98", 255),
            ("P322", "Patient322", 40, "AIDS", "135 85", 220),
            ("P323", "Patient323", 48, "AIDS", "138 88", 230),
            ("P324", "Patient324", 33, "Asthma", "126 83", 185),
            ("P325", "Patient325", 42, "Obesity", "132 85", 215),
            ("P326", "Patient326", 37, "Diabetes", "140 88", 210),
            ("P327", "Patient327", 55, "Hypertension", "150 95", 235),
            ("P328", "Patient328", 60, "Hyperlipidemia", "145 92", 250),
            ("P329", "Patient329", 41, "Autoimmune", "125 82", 205),
            ("P330", "Patient330", 49, "Cancer", "135 89", 240),
            ("P331", "Patient331", 64, "Heart Attack", "158 100", 275),
            ("P332", "Patient332", 59, "CKD", "150 94", 250),
            ("P333", "Patient333", 53, "AIDS", "140 90", 235),
            ("P334", "Patient334", 36, "Corona", "128 82", 200),
            ("P335", "Patient335", 29, "Healthy", "115 76", 170),
            ("P336", "Patient336", 46, "Obesity", "142 88", 225),
            ("P337", "Patient337", 39, "Hyperlipidemia", "136 85", 210),
            ("P338", "Patient338", 34, "Autoimmune", "122 79", 195),
            ("P339", "Patient339", 27, "Asthma", "118 77", 185),
            ("P340", "Patient340", 45, "Healthy", "120 80", 175),
        ]
        for pid, name, age, cond, bp, chol in demo_patients:
            register_patient(pid, name, age, cond, bp, chol, num_shares=5, threshold=3)
        for pid in [f"P{str(i)}" for i in range(300, 341)]:
            rec = load_record(pid)
            if rec:
                meta = load_shares(pid)
                if meta:
                    subset = meta["shares"][:meta["threshold"]]
                    key_hex = reconstruct_secret(subset)
                    unlock_patient(pid, key_hex)  # write decrypted entry for ml
        model_train()  # train model on demo data
        return {"ok": True, "msg": "Preloaded demo dataset P300 to P340"}
    except Exception as e:
        return {"error": str(e) or "Demo preload failed"}
