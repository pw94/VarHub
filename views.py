from configparser import ConfigParser
from flask import Flask
from flask_pymongo import PyMongo
from data_downloader import download_patients

appConfig = ConfigParser()
appConfig.read("config.ini")

app = Flask(__name__)
app.secret_key = appConfig.get("CoreContext", "secret_key")
app.config["MONGO_URI"] = appConfig.get("CoreContext", "mongo")
mongo = PyMongo(app)

download_patients()

if __name__ == "__main__":
    app.run()