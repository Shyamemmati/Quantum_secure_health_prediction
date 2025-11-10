import tkinter as tk
from tkinter import messagebox
from app.orchestrator import register_patient, reconstruct_key_wrapper, unlock_patient_wrapper, predict_risk

# Tkinter window setup
root = tk.Tk()
root.title("Quantum Pharma Detection - Offline")
root.geometry("600x500")
root.configure(bg="#F0F8FF")

# Patient Registration
def register_patient_action():
    pid = entry_pid.get()
    name = entry_name.get()
    age = entry_age.get()
    cond = entry_condition.get()
    bp = entry_bp.get()
    chol = entry_chol.get()

    if not pid or not name:
        messagebox.showwarning("Missing Data", "Please fill all required fields.")
        return

    res = register_patient(pid, name, int(age), cond, bp, int(chol))
    if res.get("ok"):
        messagebox.showinfo("Success", f"Patient {pid} registered successfully.")
    elif res.get("error") == "already_registered":
        messagebox.showwarning("Duplicate", f"Patient {pid} already exists.")
    else:
        messagebox.showerror("Error", res.get("error", "Unknown error."))

# Risk Prediction
def predict_risk_action():
    pid = entry_pid.get()
    res = predict_risk(pid)
    if res.get("ok"):
        msg = f"Prediction: {res['prediction']}\nRisk Score: {res.get('risk_score')}\nRisk Label: {res.get('risk_label')}"
        messagebox.showinfo("Prediction Result", msg)
    else:
        messagebox.showerror("Error", res.get("error", "Prediction failed."))

# UI Layout
tk.Label(root, text="Patient Registration", bg="#F0F8FF", font=("Arial", 16, "bold")).pack(pady=10)

frm = tk.Frame(root, bg="#F0F8FF")
frm.pack(pady=10)

tk.Label(frm, text="Patient ID:").grid(row=0, column=0, sticky="e")
entry_pid = tk.Entry(frm); entry_pid.grid(row=0, column=1)

tk.Label(frm, text="Name:").grid(row=1, column=0, sticky="e")
entry_name = tk.Entry(frm); entry_name.grid(row=1, column=1)

tk.Label(frm, text="Age:").grid(row=2, column=0, sticky="e")
entry_age = tk.Entry(frm); entry_age.grid(row=2, column=1)

tk.Label(frm, text="Condition:").grid(row=3, column=0, sticky="e")
entry_condition = tk.Entry(frm); entry_condition.grid(row=3, column=1)

tk.Label(frm, text="Blood Pressure:").grid(row=4, column=0, sticky="e")
entry_bp = tk.Entry(frm); entry_bp.grid(row=4, column=1)

tk.Label(frm, text="Cholesterol:").grid(row=5, column=0, sticky="e")
entry_chol = tk.Entry(frm); entry_chol.grid(row=5, column=1)

# Buttons
tk.Button(root, text="Register Patient", command=register_patient_action, bg="#4CAF50", fg="white").pack(pady=10)
tk.Button(root, text="Predict Risk", command=predict_risk_action, bg="#2196F3", fg="white").pack(pady=10)

root.mainloop()
