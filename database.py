from pymongo import MongoClient
from config import MONGO_URI, DB_NAME  # ✅ DB_NAME is now defined

client = MongoClient(MONGO_URI)
db = client[DB_NAME]  # ✅ Use DB_NAME correctly
