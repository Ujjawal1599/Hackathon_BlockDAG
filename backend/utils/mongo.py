from pymongo import MongoClient
import os

def get_mongo_client():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    return MongoClient(mongo_uri)

def get_chat_collection():
    client = get_mongo_client()
    db = client["metadag"]  # or your preferred db name
    return db["chat_history"]

def get_deployment_collection():
    client = get_mongo_client()
    db = client["metadag"]  # or your preferred db name
    return db["deployments"]

