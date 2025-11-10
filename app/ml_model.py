import os
import json
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

BASE_DIR = os.path.dirname(__file__)  # app folder path
DATA_DIR = os.path.join(BASE_DIR, "data")  # app data folder
DECRYPTED_PATH = os.path.join(DATA_DIR, "decrypted_patients.json")  # decrypted patients file
MODEL_PATH = os.path.join(DATA_DIR, "health_model.pkl")  # model file path

HIGH_RISK_DISEASES = {"diabetes", "hypertension", "cancer", "heart attack", "stroke", "ckd"}  # high risk set
MEDIUM_RISK_DISEASES = {"asthma", "obesity", "hyperlipidemia", "corona", "autoimmune"}  # medium risk set
LOW_RISK_DISEASES = {"healthy", "none"}  # low risk set

def _parse_bp(bp_str):  # parse blood pressure string like 120 80 or 120 80
    try:
        parts = bp_str.replace("/", " ").split()
        s = int(parts[0]) if len(parts) > 0 else 0
        d = int(parts[1]) if len(parts) > 1 else 0
        return s, d
    except Exception:
        return 0, 0

def _load_decrypted():  # load decrypted patients for ml
    if not os.path.exists(DECRYPTED_PATH):
        return {}
    with open(DECRYPTED_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def _assign_label(patient):  # assign label based on rules for initial supervision
    cond = str(patient.get("condition", "")).lower().strip()
    age = int(patient.get("age", 0))
    chol = int(patient.get("cholesterol", 0))
    systolic, diastolic = _parse_bp(patient.get("blood_pressure", "0 0"))
    if cond in HIGH_RISK_DISEASES:
        return 1
    if cond in MEDIUM_RISK_DISEASES:
        if chol > 220 or systolic > 145 or age > 60:
            return 1
        return 0
    if cond in LOW_RISK_DISEASES:
        return 0
    score = (chol / 50) + (age / 60) + (systolic / 100)
    return 1 if score > 5 else 0  # return label integer

def interpret_risk(prob):  # human friendly label for probability
    if prob >= 0.75:
        return "High Risk"
    elif prob >= 0.4:
        return "Medium Risk"
    return "Low Risk"

def train_model():  # train models and save best model
    data = _load_decrypted()
    patients = list(data.values())
    if not patients:
        return {"ok": False, "error": "No decrypted patients available"}
    X, y = [], []
    for p in patients:
        s, d = _parse_bp(p.get("blood_pressure", "0 0"))
        X.append([int(p.get("age", 0)), s, d, int(p.get("cholesterol", 0))])
        y.append(_assign_label(p))
    X, y = np.array(X), np.array(y)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    models = {
        "logistic": LogisticRegression(max_iter=1000),
        "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "svm": SVC(probability=True, kernel="rbf", random_state=42),
        "gbm": GradientBoostingClassifier(random_state=42)
    }
    best_model, best_acc = None, 0
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        if acc > best_acc:
            best_model = (model, name)
            best_acc = acc
    final_model, model_name = best_model
    joblib.dump({"model": final_model, "scaler": scaler, "type": model_name}, MODEL_PATH)
    return {"ok": True, "trained_on": len(y), "best_model": model_name, "accuracy": round(best_acc, 3)}

def predict(patient):  # predict risk for a single patient
    if not os.path.exists(MODEL_PATH):
        res = train_model()
        if not res.get("ok"):
            label = _assign_label(patient)
            return {"ok": True, "prediction": label, "risk_label": "Rule based fallback"}
    model_data = joblib.load(MODEL_PATH)
    model, scaler = model_data["model"], model_data["scaler"]
    s, d = _parse_bp(patient.get("blood_pressure", "0 0"))
    features = np.array([[int(patient.get("age", 0)), s, d, int(patient.get("cholesterol", 0))]])
    X_scaled = scaler.transform(features)
    prob = float(model.predict_proba(X_scaled)[0][1])
    pred = int(prob >= 0.5)
    risk_label = interpret_risk(prob)
    return {"ok": True, "prediction": pred, "risk_score": prob, "risk_label": risk_label}
