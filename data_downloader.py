from pymongo import MongoClient
import requests

client = MongoClient('mongodb://localhost:27017/')
db = client.var_hub

def download_patients():
    patients = db.patients

    if patients.count_documents({}) == 0:
        patients_ids = requests.get("https://junction-planreview.azurewebsites.net/api/patients").json()
        for id in patients_ids:
            patient = requests.get("https://junction-planreview.azurewebsites.net/api/patients/" + id).json()
            patients.insert_one(patient)

def download_plans():
    plans = db.plans

    if plans.count_documents({}) == 0:
        patients_ids = requests.get("https://junction-planreview.azurewebsites.net/api/patients").json()
        for id in patients_ids:
            plans_ids = requests.get("https://junction-planreview.azurewebsites.net/api/patients/" + id + "/plans").json()
            for plan_id in plans_ids:
                plan = requests.get("https://junction-planreview.azurewebsites.net/api/patients/" + id + "/plans/" + plan_id).json()
                plans.insert_one(plan)

def get_patients():
    return db.patients.find({})

def download():
    download_patients()
    download_plans()
