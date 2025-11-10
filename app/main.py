from app.orchestrator import (
    register_patient,
    reconstruct_key_wrapper,
    unlock_patient_wrapper,
    train_model,
    predict_risk,
    delete_patient_wrapper,
    reset_all_data,
    preload_demo_dataset
)

def menu():  # simple cli menu
    while True:
        print("")  # blank line
        print("Quantum Pharma Detection CLI")  # header
        print("1 Register new patient")  # option one
        print("2 Reconstruct key using shares")  # option two
        print("3 Unlock patient data cache keys")  # option three
        print("4 Train AI model")  # train model
        print("5 Predict risk for a patient")  # predict
        print("6 Delete patient data")  # delete
        print("7 Reset all data")  # reset
        print("8 Preload demo dataset and train")  # preload
        print("0 Exit")  # exit
        choice = input("Select ")  # read choice

        if choice == "1":
            pid = input("Patient ID ")
            name = input("Name ")
            age = int(input("Age "))
            cond = input("Condition ")
            bp = input("Blood Pressure eg 120 80 ")
            chol = int(input("Cholesterol "))
            res = register_patient(pid, name, age, cond, bp, chol)
            print(res)

        elif choice == "2":
            pid = input("Patient ID ")
            n = int(input("Use how many shares "))
            res = reconstruct_key_wrapper(pid, n)
            print(res)

        elif choice == "3":
            pid = input("Patient ID ")
            key_hex = input("Enter key hex ")
            res = unlock_patient_wrapper(pid, key_hex)
            print(res)

        elif choice == "4":
            res = train_model()
            print(res)

        elif choice == "5":
            pid = input("Patient ID ")
            key_hex = input("Enter key hex leave blank to use cached ").strip()
            if key_hex == "":
                key_hex = None
            res = predict_risk(pid, key_hex)
            print(res)

        elif choice == "6":
            pid = input("Patient ID ")
            res = delete_patient_wrapper(pid)
            print(res)

        elif choice == "7":
            res = reset_all_data()
            print(res)

        elif choice == "8":
            res = preload_demo_dataset()
            print(res)

        elif choice == "0":
            break

        else:
            print("Invalid choice")

if __name__ == "__main__":
    menu()
