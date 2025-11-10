import os
import streamlit as st
from app.orchestrator import (
    register_patient, reconstruct_key_wrapper, unlock_patient_wrapper,
    train_model, predict_risk, delete_patient_wrapper, preload_demo_dataset
)
from app.storage import load_decrypted_patients

# APP CONFIGURATION
st.set_page_config(page_title="Quantum Secure Health Risk Prediction", layout="wide")
st.title("Quantum Secure Health Risk Prediction")
st.caption("End-to-end secure patient data handling and AI-driven health risk prediction")

# Clean styling — larger text, default buttons
st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 20px !important;
}
</style>
""", unsafe_allow_html=True)

# INITIALIZATION
if "key_cache" not in st.session_state:
    st.session_state.key_cache = {}

if "demo_loaded" not in st.session_state:
    st.session_state.demo_loaded = False  # flag for demo data

# SIDEBAR MENU
menu = st.sidebar.selectbox(
    "Menu",
    [
        "Home",
        "Register Patient",
        "Reconstruct Key",
        "Unlock Patient",
        "Predict Risk",
        "Delete Patient",
        "System Summary"
    ],
)

# HOME PAGE
if menu == "Home":
    st.subheader("Welcome to Quantum Secure Health Risk Prediction System")
    st.write("""
    This system integrates **Quantum Key Distribution**, **Secure Multi-Party Computation (SMPC)**, 
    and **Machine Learning** to protect sensitive patient data while enabling accurate health risk predictions.
    
    Start by loading the demo dataset under **System Summary** to activate all features.
    """)

# HELPER FUNCTION FOR DEMO CHECK
def ensure_demo_loaded():
    if not st.session_state.demo_loaded:
        st.warning("Please load the demo dataset first from the 'System Summary' page.")
        return False
    return True

# REGISTER PATIENT
if menu == "Register Patient":
    st.subheader("Register New Patient")

    if not ensure_demo_loaded():
        st.stop()

    pid = st.text_input("Patient ID").strip()
    name = st.text_input("Patient Name").strip()
    age = st.number_input("Age", min_value=0, max_value=120, value=40)
    condition = st.selectbox(
        "Condition",
        ["Select Condition", "Healthy", "Asthma", "Obesity", "Hyperlipidemia",
         "Corona", "Autoimmune", "Diabetes", "Hypertension",
         "Cancer", "Heart Attack", "CKD", "AIDS"],
    )
    bp = st.text_input("Blood Pressure (e.g., 120/80)").strip()
    chol = st.text_input("Cholesterol (number)").strip()
    total_shares = st.slider("Total Shares (n)", 1, 30, 5)
    threshold = st.slider("Threshold (k)", 1, 30, 3)

    if threshold > total_shares:
        st.warning("Threshold (k) cannot be greater than total shares (n).")

    if st.button("Register and Encrypt"):
        # Better validation logic
        if not pid or not name or condition == "Select Condition" or not bp or not chol:
            st.warning("All fields are required.")
        else:
            try:
                chol_value = int(chol)
                if chol_value <= 0:
                    raise ValueError
            except ValueError:
                st.warning("Please enter a valid positive number for cholesterol.")
                chol_value = None

            if chol_value is not None:
                with st.spinner("Registering patient..."):
                    res = register_patient(pid, name, int(age), condition, bp, chol_value, total_shares, threshold)
                if res.get("error") == "already_registered":
                    st.warning(f"Patient '{pid}' already exists.")
                elif res.get("ok"):
                    st.session_state.key_cache[pid] = res.get("key_hex_for_demo", "")
                    st.success(f"Patient {pid} registered successfully.")
                    st.json({
                        "Key": res.get("key_hex_for_demo"),
                        "Threshold": res.get("threshold")
                    })
                else:
                    st.error(res.get("error", "Registration failed."))

# RECONSTRUCT KEY
elif menu == "Reconstruct Key":
    st.subheader("Reconstruct Secret Key")

    if not ensure_demo_loaded():
        st.stop()

    pid = st.text_input("Patient ID")
    k = st.number_input("Number of shares to use (K)", min_value=1, max_value=30, value=3)

    if st.button("Reconstruct"):
        if not pid:
            st.warning("Enter a patient ID.")
        else:
            res = reconstruct_key_wrapper(pid, int(k))
            if res.get("error"):
                st.error(res["error"])
            else:
                st.success(f"Key reconstructed for {pid}.")
                st.json(res)

# UNLOCK PATIENT
elif menu == "Unlock Patient":
    st.subheader("Unlock Patient Data")

    if not ensure_demo_loaded():
        st.stop()

    pid = st.text_input("Patient ID")
    key_hex = st.text_area("Key Hex (leave blank to use cached key)")

    if st.button("Unlock Data"):
        use_key = key_hex.strip() or st.session_state.key_cache.get(pid)
        if not use_key:
            st.warning("No key found. Reconstruct key first.")
        else:
            res = unlock_patient_wrapper(pid, use_key)
            if res.get("ok"):
                st.session_state.key_cache[pid] = use_key
                st.success(f"Patient {pid} unlocked successfully.")
                st.json(res["patient"])
            else:
                st.error(res.get("error", "Failed to unlock patient."))

# PREDICT RISK
elif menu == "Predict Risk":
    st.subheader("Predict Patient Health Risk")

    if not ensure_demo_loaded():
        st.stop()

    pid = st.text_input("Patient ID")
    key_hex = st.text_area("Key Hex (leave blank to use cached key)")
    use_key = key_hex.strip() or st.session_state.key_cache.get(pid)

    if st.button("Predict Risk"):
        if not pid:
            st.warning("Enter a patient ID.")
        else:
            res = predict_risk(pid, use_key)

            if (not res.get("ok")) or ("Model not trained" in str(res.get("risk_label"))):
                st.warning("Model not ready. Retraining...")
                train_result = train_model()
                if train_result.get("ok"):
                    st.success("Model retrained successfully.")
                    res = predict_risk(pid, use_key)
                else:
                    st.error("Model training failed.")

            if res.get("ok"):
                risk_label = str(res.get("risk_label")).lower()
                risk_score = res.get("risk_score", 0)

                # Human-readable interpretation
                if "high" in risk_label:
                    meaning = "High Risk — requires immediate attention."
                elif "medium" in risk_label:
                    meaning = "Medium Risk — patient should be monitored regularly."
                else:
                    meaning = "Low Risk — condition appears stable."

                st.success("Prediction completed successfully.")
                st.write(f"**Risk Label:** {res.get('risk_label')}")
                st.write(f"**Risk Score:** {round(risk_score, 3)}")
                st.info(meaning)

            else:
                st.error(res.get("error", "Unable to predict."))

# SYSTEM SUMMARY
elif menu == "System Summary":
    st.subheader("System Summary and Dataset Control")

    if st.button("Load Demo Dataset"):
        with st.spinner("Loading demo dataset and training model..."):
            res = preload_demo_dataset()
        if res.get("ok"):
            st.session_state.demo_loaded = True
            st.success("Demo dataset loaded successfully. All features are now enabled.")
        else:
            st.error(res.get("error", "Failed to load demo dataset."))

    patients = load_decrypted_patients()

    if not st.session_state.demo_loaded:
        st.info("Demo dataset not loaded yet. Load it above to enable system functions.")
    elif not patients:
        st.info("No patient data available.")
    else:
        st.write(f"Total patients: {len(patients)}")
        for pid, pdata in patients.items():
            with st.expander(f"Patient ID: {pid}", expanded=False):
                st.json(pdata)

    if st.button("Refresh"):
        st.rerun()

# FOOTER
st.markdown("---")
st.caption("Developed for Secure AI Project | Quantum Secure Health Risk Prediction | End-to-End Demo")
