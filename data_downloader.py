from pymongo import MongoClient
import requests
import json

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

def get_patient(id):
    return db.patients.find_one({'Id': id})

def get_patient_plans_ids(id):
    return [plan['Id'] for plan in db.patients.find_one({'Id': id})['Plans']]

def put_test_to_db():
    tests = db.tests
    if tests.count_documents({}) == 0:
        with open('tests.json', 'r') as infile:
            data = json.loads(infile.read())
            for datum in data:
                if isinstance(datum, dict):
                    tests.insert_many(datum)

def download():
    put_test_to_db()
    download_patients()
    download_plans()