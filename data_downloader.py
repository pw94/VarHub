from pymongo import MongoClient
import requests

def download_patients():
    client = MongoClient('mongodb://localhost:27017/')
    db = client.var_hub
    patients = db.patients

    if patients.count_documents({}) == 0:
        patients_ids = requests.get("https://junction-planreview.azurewebsites.net/api/patients").json()
        for id in patients_ids:
            patient = requests.get("https://junction-planreview.azurewebsites.net/api/patients/" + id).json()
            patients.insert_one(patient)
