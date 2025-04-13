import os
from pymongo import MongoClient
from groq import Groq

# ✅ MongoDB Connection with SSL Fix
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://dhruvdawar11022006:dd110206@cluster0.gohdq.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true"
)
DB_NAME = os.getenv("DB_NAME", "intellica_courses")

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ MongoDB Connection Failed: {e}")

# ✅ Groq AI Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")  # Use an actual key
groq_client = Groq(api_key=GROQ_API_KEY)

# ✅ SMTP Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = 587
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "harshsharmaa990@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "gncqwoyeibggmjxz")  # ⚠️ Use an App Password, not your real password

