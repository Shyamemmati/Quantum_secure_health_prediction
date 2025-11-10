def input_patient_data(patient_id: str):  # interactive data input for a patient
    name = input("Name ")  # patient name
    age = int(input("Age "))  # patient age
    condition = input("Condition ")  # medical condition name
    blood_pressure = input("Blood Pressure eg 120 80 ")  # blood pressure text
    cholesterol = int(input("Cholesterol "))  # cholesterol as integer
    return {
        "id": patient_id,
        "name": name,
        "age": age,
        "condition": condition,
        "blood_pressure": blood_pressure,
        "cholesterol": cholesterol
    }  # return patient dict
